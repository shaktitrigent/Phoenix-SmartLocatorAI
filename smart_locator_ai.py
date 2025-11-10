#!/usr/bin/env python3
"""
SmartLocatorAI - Unified pipeline for DOM scan, locator generation, reporting, and POM export.

Outputs (default):
  exports/report.md
  exports/locators.json
  exports/playwright_page.py
  exports/selenium_page.py
"""

import argparse
import json
import os
from typing import Any, Dict, List

from dom_scanner import (
    scan_dom,
    generate_locators_from_elements,
    to_markdown_table,
    compute_summary,
)
from page_object_exporter import (
    generate_playwright_pom,
    generate_selenium_pom,
)


STABILITY_ORDER = {"low": 1, "medium": 2, "high": 3}


class SmartLocatorAI:
    def __init__(self, exports_dir: str = "exports") -> None:
        self.exports_dir = exports_dir
        os.makedirs(self.exports_dir, exist_ok=True)

    def _filter_by_min_stability(self, locators: List[Dict[str, Any]], min_label: str) -> List[Dict[str, Any]]:
        if not min_label:
            return locators
        threshold = STABILITY_ORDER.get(min_label.lower(), 1)
        filtered: List[Dict[str, Any]] = []
        for l in locators:
            label = (l.get("stability") or "").lower()
            score_label = STABILITY_ORDER.get(label, 1)
            if score_label >= threshold:
                filtered.append(l)
        return filtered

    def run(
        self,
        html_or_url: str,
        framework: str = "both",
        min_stability: str = "",
        use_js: bool = False,
        class_name: str = "ProductPage",
        validate: bool = False,
        auth_opts: Dict[str, Any] | None = None,
        use_gemini: bool = False,
    ) -> Dict[str, str]:
        # 1) Scan DOM
        elements = scan_dom(html_or_url, js_render=use_js)

        # 2) Generate locators
        locators = generate_locators_from_elements(elements)

        # 3) Optional filtering by stability
        if min_stability:
            locators = self._filter_by_min_stability(locators, min_stability)

        # 3b) Optional validation (URL only)
        if validate and (html_or_url.startswith("http://") or html_or_url.startswith("https://")):
            locators = self._validate_locators_with_playwright(html_or_url, locators, auth_opts or {})

        # 3c) Optional Gemini enrichment
        ai_enrichment: Dict[str, Any] | None = None
        if use_gemini:
            ai_enrichment = self._enrich_with_gemini(html_or_url, elements, locators)

        # 4) Exports
        # 4a) JSON with integration metadata
        json_path = os.path.join(self.exports_dir, "locators.json")
        from datetime import datetime
        summary = compute_summary(locators, total_elements=len(elements))
        json_payload: Dict[str, Any] = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": html_or_url if html_or_url.startswith("http") else "html_content",
                "total_elements": len(elements),
                "total_locators": len(locators),
                "framework": framework,
                "min_stability": min_stability or "None",
                "validated": validate,
                "ai_enriched": use_gemini,
                "class_name": class_name,
            },
            "summary": summary,
            "locators": locators,
        }
        if ai_enrichment:
            json_payload["ai_enrichment"] = ai_enrichment
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2, ensure_ascii=False)

        # 4b) Markdown report (table + summary)
        md_path = os.path.join(self.exports_dir, "report.md")
        summary = compute_summary(locators, total_elements=len(elements))
        md = []
        md.append("# Smart Locator AI Report\n\n")
        md.append("## Summary\n\n")
        md.append("```json\n" + json.dumps(summary, indent=2, ensure_ascii=False) + "\n```\n\n")
        # AI section if present
        if ai_enrichment:
            md.append("## AI Analysis (Gemini)\n\n")
            md.append("### Analysis\n\n")
            md.append("```json\n" + json.dumps(ai_enrichment.get("analysis", {}), indent=2, ensure_ascii=False) + "\n```\n\n")
            code = ai_enrichment.get("code", {})
            if code:
                md.append("### AI-Generated Code\n\n")
                if code.get("selenium"):
                    md.append("#### Selenium (Python)\n\n")
                    md.append("```python\n" + code.get("selenium", "") + "\n```\n\n")
                if code.get("playwright"):
                    md.append("#### Playwright (Python)\n\n")
                    md.append("```python\n" + code.get("playwright", "") + "\n```\n\n")
                if code.get("cypress"):
                    md.append("#### Cypress (JavaScript)\n\n")
                    md.append("```javascript\n" + code.get("cypress", "") + "\n```\n\n")

        md.append("## Locators\n\n")
        md.append(to_markdown_table(locators))
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("".join(md))

        # 4c) Page Objects
        out_paths: Dict[str, str] = {"json": json_path, "markdown": md_path}
        
        # Generate framework-specific Page Objects
        if framework.lower() in ("both", "playwright"):
            pw_code = generate_playwright_pom(locators, class_name=class_name)
            pw_path = os.path.join(self.exports_dir, f"{class_name}_Playwright.py")
            with open(pw_path, "w", encoding="utf-8") as f:
                f.write(pw_code)
            out_paths["playwright_pom"] = pw_path
            
        if framework.lower() in ("both", "selenium"):
            se_code = generate_selenium_pom(locators, class_name=class_name)
            se_path = os.path.join(self.exports_dir, f"{class_name}_Selenium.py")
            with open(se_path, "w", encoding="utf-8") as f:
                f.write(se_code)
            out_paths["selenium_pom"] = se_path

        return out_paths

    def _enrich_with_gemini(
        self,
        html_or_url: str,
        elements: List[Dict[str, Any]],
        locators: List[Dict[str, Any]],
    ) -> Dict[str, Any] | None:
        try:
            import os
            import requests
            import google.generativeai as genai
        except Exception:
            return None

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
        except Exception:
            return None

        # Fetch HTML if URL
        html_sample = ""
        if html_or_url.startswith("http://") or html_or_url.startswith("https://"):
            try:
                r = requests.get(html_or_url, timeout=20)
                if r.ok:
                    html_sample = r.text[:2000]
            except Exception:
                html_sample = ""
        else:
            # if raw html provided
            if "<" in html_or_url and ">" in html_or_url:
                html_sample = html_or_url[:2000]

        # Build locator summary
        def summarize_locators(ls: List[Dict[str, Any]]) -> str:
            out = []
            for l in ls[:50]:
                out.append(f"{l.get('custom_name','')} | {l.get('locator_type','')} | {l.get('locator_value','')}")
            return "\n".join(out)

        locator_summary = summarize_locators(locators)

        # Analysis prompt
        analysis_prompt = f"""
Analyze the following page HTML and locator summary for test automation quality.

HTML (truncated):
{html_sample}

Locators:
{locator_summary}

Return STRICT JSON with keys:
- page_type (string)
- element_quality_score (1-10)
- best_strategies (string[])
- potential_issues (string[])
- best_practices_compliance (1-10)
- maintenance_risk_score (1-10)
- overall_recommendations (string[])
"""
        analysis = {}
        try:
            resp = model.generate_content(analysis_prompt)
            txt = (resp.text or "").strip()
            if txt.startswith("{") and txt.endswith("}"):
                analysis = json.loads(txt)
            else:
                analysis = {"overall_recommendations": [txt]}
        except Exception:
            analysis = {}

        # Code prompt
        code_prompt = f"""
Generate production-ready test automation code for these locators.

Provide JSON with keys 'selenium', 'playwright', 'cypress'.
Write idiomatic Page Object methods, waits, and clear names.

Locators:
{locator_summary}
"""
        code = {}
        try:
            resp = model.generate_content(code_prompt)
            txt = (resp.text or "").strip()
            if txt.startswith("{") and txt.endswith("}"):
                code = json.loads(txt)
            else:
                code = {
                    "selenium": txt[:1200],
                    "playwright": txt[:1200],
                    "cypress": txt[:1200],
                }
        except Exception:
            code = {}

        return {"analysis": analysis, "code": code}

    def _validate_locators_with_playwright(
        self,
        url: str,
        locators: List[Dict[str, Any]],
        auth_opts: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Validate locators in a real browser using Playwright.
        Auth options supported:
          - storage_state: path to storage state JSON
          - simple login: auth_url, user, password, user_selector, pass_selector, submit_selector,
                          auth_wait_selector or auth_wait_url_contains
        """
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            # Mark validation_error for all
            for l in locators:
                l.setdefault("validated", False)
                l.setdefault("match_count", 0)
                l["validation_error"] = "Playwright not available"
            return locators

        storage_state = auth_opts.get("storage_state")
        auth_url = auth_opts.get("auth_url")
        user = auth_opts.get("user")
        password = auth_opts.get("password")
        user_sel = auth_opts.get("user_selector")
        pass_sel = auth_opts.get("pass_selector")
        submit_sel = auth_opts.get("submit_selector")
        wait_sel = auth_opts.get("auth_wait_selector")
        wait_url_part = auth_opts.get("auth_wait_url_contains")

        def parse_role_selector(expr: str) -> tuple[str, str] | None:
            # example: page.getByRole('button', { name: 'Add to Cart' })
            import re
            m = re.search(r"getByRole\('\s*([^']+)\s*'\s*,\s*\{\s*name:\s*'([^']+)'\s*\}\)", expr)
            if not m:
                return None
            return m.group(1), m.group(2)

        def parse_text_selector(expr: str) -> str | None:
            # example: page.getByText('Some Text')
            import re
            m = re.search(r"getByText\('\s*([^']+)\s*'\)", expr)
            if not m:
                return None
            return m.group(1)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context_args: Dict[str, Any] = {}
            if storage_state and os.path.exists(storage_state):
                context_args["storage_state"] = storage_state
            context = browser.new_context(**context_args)
            page = context.new_page()

            # Perform simple login if requested and no storage state provided
            if not context_args and auth_url and user is not None and password is not None and user_sel and pass_sel and submit_sel:
                page.goto(auth_url)
                page.fill(user_sel, str(user))
                page.fill(pass_sel, str(password))
                page.click(submit_sel)
                if wait_sel:
                    page.wait_for_selector(wait_sel, timeout=30000)
                elif wait_url_part:
                    page.wait_for_url(f"**{wait_url_part}**", timeout=30000)

            # Navigate to target URL
            page.goto(url)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

            # Validate each locator
            for l in locators:
                l.setdefault("validated", False)
                l.setdefault("match_count", 0)
                l.pop("validation_error", None)
                lt = (l.get("locator_type") or "").lower()
                val = l.get("locator_value") or ""
                try:
                    if lt == "css selector":
                        locator = page.locator(val)
                    elif lt == "xpath":
                        locator = page.locator(f"xpath={val}")
                    elif "role selector" in lt:
                        parsed = parse_role_selector(val)
                        if not parsed:
                            l["validation_error"] = "Unable to parse getByRole"
                            continue
                        role, name = parsed
                        locator = page.get_by_role(role, name=name)
                    elif "text selector" in lt:
                        text = parse_text_selector(val)
                        if text is None:
                            l["validation_error"] = "Unable to parse getByText"
                            continue
                        locator = page.get_by_text(text)
                    else:
                        l["validation_error"] = "Unknown locator_type"
                        continue

                    count = locator.count()
                    l["match_count"] = int(count)
                    l["validated"] = bool(count == 1)
                except Exception as ve:
                    l["validation_error"] = str(ve)

            context.close()
            browser.close()

        return locators


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Locator AI unified pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", type=str, help="Target page URL")
    group.add_argument("--file", type=str, help="Local HTML file")
    group.add_argument("--html", type=str, help="Raw HTML content")
    parser.add_argument("--framework", choices=["both", "playwright", "selenium"], default="both", help="Which POMs to export")
    parser.add_argument("--min-stability", choices=["High", "Medium", "Low"], default="", help="Filter locators below a stability label")
    parser.add_argument("--js", action="store_true", help="Use Playwright rendering when scanning URL (if installed)")
    parser.add_argument("--class-name", default="ProductPage", help="Page Object class name")
    parser.add_argument("--validate", action="store_true", help="Validate locators in real browser (URL inputs only)")
    parser.add_argument("--gemini", action="store_true", help="Enrich report with Gemini AI analysis and code recommendations")
    # Auth options
    parser.add_argument("--auth-storage-state", help="Playwright storage state JSON path")
    parser.add_argument("--auth-url", help="Login URL for simple auth flow")
    parser.add_argument("--auth-user", help="Username for simple auth flow")
    parser.add_argument("--auth-pass", help="Password for simple auth flow")
    parser.add_argument("--user-selector", help="Selector for username field")
    parser.add_argument("--pass-selector", help="Selector for password field")
    parser.add_argument("--submit-selector", help="Selector for login submit button")
    parser.add_argument("--auth-wait-selector", help="Selector to wait for post-login")
    parser.add_argument("--auth-wait-url-contains", help="Substring of URL to wait for after login")
    args = parser.parse_args()

    target = args.url or args.file or args.html
    runner = SmartLocatorAI()
    auth_opts = {
        "storage_state": args.auth_storage_state,
        "auth_url": args.auth_url,
        "user": args.auth_user,
        "password": args.auth_pass,
        "user_selector": args.user_selector,
        "pass_selector": args.pass_selector,
        "submit_selector": args.submit_selector,
        "auth_wait_selector": args.auth_wait_selector,
        "auth_wait_url_contains": args.auth_wait_url_contains,
    }
    result_paths = runner.run(
        target,
        framework=args.framework,
        min_stability=args.min_stability,
        use_js=args.js,
        class_name=args.class_name,
        validate=args.validate,
        auth_opts=auth_opts,
        use_gemini=args.gemini,
    )
    print(json.dumps(result_paths, indent=2))


if __name__ == "__main__":
    main()


