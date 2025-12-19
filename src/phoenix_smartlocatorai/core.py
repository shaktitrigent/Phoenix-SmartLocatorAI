"""
Core API for Phoenix Smart Locator AI
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from phoenix_smartlocatorai.dom_scanner import (
    scan_dom,
    generate_locators_from_elements,
    compute_summary,
)
from phoenix_smartlocatorai.page_object_exporter import (
    generate_playwright_pom,
    generate_selenium_pom,
)


STABILITY_ORDER = {"low": 1, "medium": 2, "high": 3}


def generate_locators_from_dom(
    input_html_or_url: Union[str, Path],
    frameworks: Optional[List[str]] = None,
    output_dir: Union[str, Path] = ".",
    class_name: str = "Page",
    min_stability: Optional[str] = None,
    use_js: bool = False,
    validate: bool = False,
    auth_opts: Optional[Dict[str, Any]] = None,
    use_gemini: bool = False,
) -> Dict[str, str]:
    """
    Generate locators from DOM (HTML file or URL) and create page.py and locators.json.
    
    Args:
        input_html_or_url: Path to HTML file or URL to scan
        frameworks: List of frameworks to generate (e.g., ["Playwright", "Selenium"])
                   Defaults to ["Playwright", "Selenium"]
        output_dir: Directory to write outputs (default: current directory)
        class_name: Name for the Page Object class (default: "Page")
        min_stability: Minimum stability filter ("High", "Medium", "Low") or None
        use_js: Use Playwright to render JavaScript (for URL inputs)
        validate: Validate locators in real browser (URL inputs only)
        auth_opts: Authentication options for validation
        use_gemini: Enable Gemini AI enrichment
    
    Returns:
        Dictionary with paths to generated files:
        {
            "locators_json": "path/to/locators.json",
            "page_py": "path/to/page.py",  # Only if single framework
            "playwright_pom": "path/to/Page_Playwright.py",  # If Playwright requested
            "selenium_pom": "path/to/Page_Selenium.py",  # If Selenium requested
        }
    """
    if frameworks is None:
        frameworks = ["Playwright", "Selenium"]
    
    # Normalize frameworks to lowercase
    frameworks = [f.lower() for f in frameworks]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert Path to string for compatibility
    input_str = str(input_html_or_url)
    
    # 1) Scan DOM
    elements = scan_dom(input_str, js_render=use_js)
    
    # 2) Generate locators
    locators = generate_locators_from_elements(elements)
    
    # 3) Optional filtering by stability
    if min_stability:
        threshold = STABILITY_ORDER.get(min_stability.lower(), 1)
        filtered = []
        for loc in locators:
            label = (loc.get("stability") or "").lower()
            score_label = STABILITY_ORDER.get(label, 1)
            if score_label >= threshold:
                filtered.append(loc)
        locators = filtered
    
    # 4) Optional validation (URL only)
    if validate and (input_str.startswith("http://") or input_str.startswith("https://")):
        locators = _validate_locators_with_playwright(input_str, locators, auth_opts or {})
    
    # 5) Optional Gemini enrichment
    ai_enrichment = None
    if use_gemini:
        ai_enrichment = _enrich_with_gemini(input_str, elements, locators)
    
    # 6) Generate outputs
    result_paths: Dict[str, str] = {}
    
    # 6a) Generate locators.json
    summary = compute_summary(locators, total_elements=len(elements))
    json_path = output_dir / "locators.json"
    json_payload: Dict[str, Any] = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source": input_str if input_str.startswith("http") else "html_content",
            "total_elements": len(elements),
            "total_locators": len(locators),
            "frameworks": frameworks,
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
    result_paths["locators_json"] = str(json_path)
    
    # 6b) Generate Page Objects
    if "playwright" in frameworks:
        pw_code = generate_playwright_pom(locators, class_name=class_name)
        pw_path = output_dir / f"{class_name}_Playwright.py"
        with open(pw_path, "w", encoding="utf-8") as f:
            f.write(pw_code)
        result_paths["playwright_pom"] = str(pw_path)
        
        # If only Playwright, also create page.py
        if len(frameworks) == 1:
            page_py_path = output_dir / "page.py"
            with open(page_py_path, "w", encoding="utf-8") as f:
                f.write(pw_code)
            result_paths["page_py"] = str(page_py_path)
    
    if "selenium" in frameworks:
        se_code = generate_selenium_pom(locators, class_name=class_name)
        se_path = output_dir / f"{class_name}_Selenium.py"
        with open(se_path, "w", encoding="utf-8") as f:
            f.write(se_code)
        result_paths["selenium_pom"] = str(se_path)
        
        # If only Selenium, also create page.py
        if len(frameworks) == 1:
            page_py_path = output_dir / "page.py"
            with open(page_py_path, "w", encoding="utf-8") as f:
                f.write(se_code)
            result_paths["page_py"] = str(page_py_path)
    
    return result_paths


def _validate_locators_with_playwright(
    url: str,
    locators: List[Dict[str, Any]],
    auth_opts: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Validate locators in a real browser using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
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
    
    def parse_role_selector(expr: str):
        import re
        m = re.search(r"getByRole\('\s*([^']+)\s*'\s*,\s*\{\s*name:\s*'([^']+)'\s*\}\)", expr)
        if not m:
            return None
        return m.group(1), m.group(2)
    
    def parse_text_selector(expr: str):
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
        
        if not context_args and auth_url and user is not None and password is not None and user_sel and pass_sel and submit_sel:
            page.goto(auth_url)
            page.fill(user_sel, str(user))
            page.fill(pass_sel, str(password))
            page.click(submit_sel)
            if wait_sel:
                page.wait_for_selector(wait_sel, timeout=30000)
            elif wait_url_part:
                page.wait_for_url(f"**{wait_url_part}**", timeout=30000)
        
        page.goto(url)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        
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


def _enrich_with_gemini(
    html_or_url: str,
    elements: List[Dict[str, Any]],
    locators: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Enrich with Gemini AI analysis."""
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
    
    html_sample = ""
    if html_or_url.startswith("http://") or html_or_url.startswith("https://"):
        try:
            r = requests.get(html_or_url, timeout=20)
            if r.ok:
                html_sample = r.text[:2000]
        except Exception:
            html_sample = ""
    else:
        if "<" in html_or_url and ">" in html_or_url:
            html_sample = html_or_url[:2000]
    
    def summarize_locators(ls: List[Dict[str, Any]]) -> str:
        out = []
        for l in ls[:50]:
            out.append(f"{l.get('custom_name','')} | {l.get('locator_type','')} | {l.get('locator_value','')}")
        return "\n".join(out)
    
    locator_summary = summarize_locators(locators)
    
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


