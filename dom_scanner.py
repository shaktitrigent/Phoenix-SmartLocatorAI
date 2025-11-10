#!/usr/bin/env python3
"""
DOM Scanner
Goal: Build a lightweight DOM crawler that scans any web page (live URL or local HTML)
and extracts interactable elements (buttons, links, inputs, etc.) with their attributes.

Usage (module):
    from dom_scanner import scan_dom
    elements = scan_dom("https://example.com")

CLI:
    python dom_scanner.py --url https://example.com
    python dom_scanner.py --file ./page.html
    python dom_scanner.py --url https://example.com --js  # attempt JS render via Playwright if available

Output: JSON list of element dictionaries
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


INTERACTABLE_TAGS = {"a", "button", "input", "select", "textarea"}


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _load_html_from_url(url: str, timeout: int = 20) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _load_html_with_playwright(url: str, timeout_ms: int = 20000) -> Optional[str]:
    """Attempt to render page with Playwright if installed. Returns HTML or None on failure."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="load")
            # Try to wait for network idle to capture post-load DOM if possible
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass
            content = page.content()
            context.close()
            browser.close()
            return content
    except Exception:
        return None


def _normalize_text(text: str) -> str:
    if text is None:
        return ""
    # Collapse whitespace and trim
    return re.sub(r"\s+", " ", text).strip()


def _collect_data_attributes(attrs: Dict[str, Any]) -> Dict[str, Any]:
    data_attrs: Dict[str, Any] = {}
    for key, value in attrs.items():
        if isinstance(key, str) and key.startswith("data-"):
            data_attrs[key] = value
    return data_attrs


def _element_to_record(el, soup: BeautifulSoup) -> Dict[str, Any]:
    tag = el.name or ""
    attrs = dict(el.attrs or {})

    # Normalize class to space-separated string
    _class = attrs.get("class")
    if isinstance(_class, list):
        class_str = " ".join(_class)
    elif isinstance(_class, str):
        class_str = _class
    else:
        class_str = ""

    # Attempt to find associated label text for inputs/selects/textarea
    label_text = ""
    if (el.name in {"input", "select", "textarea"}):
        el_id = attrs.get("id")
        if el_id and soup is not None:
            lbl = soup.find("label", attrs={"for": el_id})
            if lbl:
                label_text = _normalize_text(lbl.get_text(separator=" ", strip=True))
        if not label_text:
            parent_label = el.find_parent("label")
            if parent_label:
                label_text = _normalize_text(parent_label.get_text(separator=" ", strip=True))

    record: Dict[str, Any] = {
        "tag": tag,
        "id": attrs.get("id") or "",
        "name": attrs.get("name") or "",
        "class": class_str,
        "text": _normalize_text(el.get_text(separator=" ", strip=True) if tag != "input" else (attrs.get("value") or "")),
        "aria-label": attrs.get("aria-label") or "",
        "role": attrs.get("role") or "",
    }
    if label_text:
        record["label_text"] = label_text

    # Useful extras by tag
    if tag == "a":
        record["href"] = attrs.get("href") or ""
    if tag == "input":
        record["type"] = attrs.get("type") or ""
        record["value"] = attrs.get("value") or ""
        record["placeholder"] = attrs.get("placeholder") or ""
    if tag in {"textarea", "select"}:
        record["placeholder"] = attrs.get("placeholder") or ""

    # Include all data-* attributes
    data_attrs = _collect_data_attributes(attrs)
    if data_attrs:
        record["data"] = data_attrs

    # Remove empty keys for cleanliness
    cleaned = {k: v for k, v in record.items() if v not in (None, "")}
    return cleaned


def extract_interactable_elements(html: str) -> List[Dict[str, Any]]:
    """Parse HTML and extract interactable elements with key attributes."""
    soup = BeautifulSoup(html, "lxml")

    elements: List[Dict[str, Any]] = []
    for tag in INTERACTABLE_TAGS:
        for el in soup.find_all(tag):
            elements.append(_element_to_record(el, soup))

    return elements


def _to_camel_case(s: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", s or "")
    return "".join(p.capitalize() for p in parts if p)


def _guess_custom_name(elem: Dict[str, Any]) -> str:
    tag = elem.get("tag", "")
    id_val = elem.get("id", "")
    classes = elem.get("class", "")
    text = (elem.get("text") or "").strip()
    aria = (elem.get("aria-label") or "").strip()
    label_text = (elem.get("label_text") or "").strip()
    placeholder = (elem.get("placeholder") or "").strip()
    data = elem.get("data", {}) or {}

    # Prefer human-visible names first
    visible_name = ""
    if tag in {"button", "a"} and text:
        visible_name = text
    elif label_text:
        visible_name = label_text
    elif aria:
        visible_name = aria
    elif placeholder and tag in {"input", "textarea"}:
        visible_name = placeholder

    base = ""
    if visible_name:
        base = _to_camel_case(visible_name)
    elif "data-test" in data:
        base = _to_camel_case(str(data.get("data-test")))
    elif id_val:
        base = _to_camel_case(id_val)
    elif classes:
        base = _to_camel_case(classes.split(" ")[0])
    else:
        base = _to_camel_case(tag)

    suffix = {
        "a": "Link",
        "button": "Button",
        "input": "Input",
        "select": "Select",
        "textarea": "Textarea",
    }.get(tag, "Element")

    if base.endswith(suffix):
        return base
    return f"{base}{suffix}"


def _css_selector_for(elem: Dict[str, Any], id_counts: Dict[str, int]) -> Dict[str, str]:
    tag = elem.get("tag", "")
    elem_id = elem.get("id")
    classes = elem.get("class", "")
    data = elem.get("data", {}) or {}

    # Prefer unique ID
    if elem_id:
        is_unique = id_counts.get(elem_id, 0) == 1
        if is_unique:
            return {"selector": f"#{elem_id}", "stability": "High", "type": "CSS Selector"}
        # Non-unique id falls through to other strategies

    # Prefer data-test exact match if present
    if "data-test" in data:
        val = str(data["data-test"]).replace("'", "\\'")
        return {"selector": f"[{"data-test"}='{val}']", "stability": "High", "type": "CSS Selector"}

    # Fall back to class partial match (Medium)
    if classes:
        first_class = classes.split(" ")[0]
        if first_class:
            val = first_class.replace("'", "\\'")
            return {"selector": f"[class*='{val}']", "stability": "Medium", "type": "CSS Selector"}

    # Last resort: tag selector (Low)
    return {"selector": tag or "*", "stability": "Low", "type": "CSS Selector"}


def _xpath_selector_for(elem: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, str]:
    tag = elem.get("tag", "")
    text = (elem.get("text") or "").strip()

    # Text exact match when short and safe
    if tag and text and len(text) <= 60 and "\n" not in text and "'" not in text:
        return {"selector": f"//{tag}[text()='{text}']", "stability": "Medium", "type": "XPath"}

    # Fallback: indexed XPath among same-tag siblings (Low)
    if tag:
        # Count position among same tag occurrences in document order
        index = 1
        count = 0
        for el in soup.find_all(tag):
            count += 1
            # approximate matching by comparing key attributes
            if (el.get("id") == elem.get("id") and
                ("class" in el.attrs and "class" in elem and " ".join(el.get("class", [])) == elem.get("class", "")) and
                _normalize_text(el.get_text(separator=" ", strip=True)) == elem.get("text", "")):
                index = count
                break
        return {"selector": f"//{tag}[{index}]", "stability": "Low", "type": "XPath"}

    return {"selector": "//*", "stability": "Low", "type": "XPath"}


def _playwright_role_selector_for(elem: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate a Playwright role/text-based selector when possible.
    Prefer getByRole if we can infer role; else getByText for links/buttons with text.
    """
    tag = elem.get("tag", "")
    role = elem.get("role")
    text = (elem.get("text") or "").strip()
    aria_label = elem.get("aria-label")

    inferred_role = role
    if not inferred_role:
        if tag == "a":
            inferred_role = "link"
        elif tag == "button":
            inferred_role = "button"
        elif tag == "input":
            inferred_role = "textbox" if (elem.get("type") in (None, "", "text", "search", "email", "password")) else None

    # Prefer name from aria-label, else visible text
    name = (aria_label or text or "").strip()
    if inferred_role and name:
        # page.getByRole('button', { name: 'Add to Cart' })
        safe_name = name.replace("'", "\\'")
        return {
            "selector": f"page.getByRole('{inferred_role}', {{ name: '{safe_name}' }})",
            "stability": "High",
            "type": "Role Selector",
        }

    # Fallback: getByText for links/buttons
    if tag in {"a", "button"} and text:
        safe_text = text.replace("'", "\\'")
        return {
            "selector": f"page.getByText('{safe_text}')",
            "stability": "Medium",
            "type": "Text Selector",
        }

    return None


def _automation_tool_for(locator_type: str, locator_value: str) -> str:
    lt = locator_type.lower()
    if "role" in lt or "text selector" in lt:
        return "Playwright"
    if lt == "css selector":
        return "Both"
    if lt == "xpath":
        return "Selenium"
    # Default safe
    return "Both"


def _generate_code_snippets(locator_type: str, locator_value: str, automation_tool: str) -> Dict[str, str]:
    """Produce ready-to-copy Python snippets for Playwright and/or Selenium."""
    lt = locator_type.lower()
    code: Dict[str, str] = {}

    # Playwright code
    if automation_tool in ("Playwright", "Both"):
        if "role" in lt:  # Role Selector: value already like page.getByRole('button', { name: 'X' })
            code["playwright_code"] = f"{locator_value}.click()"
        elif "text selector" in lt:  # page.getByText('X')
            code["playwright_code"] = f"{locator_value}.click()"
        elif lt == "css selector":
            # use page.locator("<css>")
            safe = locator_value.replace("\\", "\\\\").replace("\"", "\\\"")
            code["playwright_code"] = f"page.locator(\"{safe}\").click()"
        elif lt == "xpath":
            # Playwright can use XPath with locator("xpath=...")
            safe = locator_value.replace("\\", "\\\\").replace("\"", "\\\"")
            code["playwright_code"] = f"page.locator(\"xpath={safe}\").click()"

    # Selenium code
    if automation_tool in ("Selenium", "Both"):
        if lt == "css selector":
            safe = locator_value.replace("\\", "\\\\").replace("\"", "\\\"")
            code["selenium_code"] = f"driver.find_element(By.CSS_SELECTOR, \"{safe}\").click()"
        elif lt == "xpath":
            safe = locator_value.replace("\\", "\\\\").replace("\"", "\\\"")
            code["selenium_code"] = f"driver.find_element(By.XPATH, \"{safe}\").click()"
        # Role/Text selectors are Playwright-specific; omit for Selenium

    return code


def _label_from_score(score: int) -> str:
    if score >= 8:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def _compute_stability_score(
    elem: Dict[str, Any], locator_type: str, locator_value: str, id_counts: Dict[str, int]
) -> int:
    """Compute numeric stability score (1-10) based on rules.

    High (8-10): Unique id, data-testid/test, or role+name combo
    Medium (5-7): Non-unique class, partial attr match, exact text xpath
    Low (1-4): Indexed XPath, tag-only, or missing semantic attributes
    """
    score = 5  # start neutral

    lt = locator_type.lower()
    val = locator_value or ""
    elem_id = elem.get("id")
    data = elem.get("data", {}) or {}
    role = elem.get("role")
    name = (elem.get("aria-label") or elem.get("text") or "").strip()
    classes = (elem.get("class") or "").strip()

    # High confidence signals
    if elem_id and id_counts.get(elem_id, 0) == 1 and lt == "css selector" and val.startswith("#"):
        score = 10
    elif any(k in data for k in ("data-testid", "data-testid", "data-test")) and lt == "css selector":
        score = 9
    elif ("role selector" in lt) and role and name:
        score = 9

    # XPath signals
    elif lt == "xpath":
        if "text()=" in val or "text()='" in val:
            score = 6
        # indexed xpath pattern //tag[n]
        if re.search(r"//[a-zA-Z]+\[\d+\]", val):
            score = min(score, 2)

    # CSS generic signals
    elif lt == "css selector":
        if val.startswith("[class*") or (classes and not elem_id and not data):
            score = 6
        elif val in {elem.get("tag", ""), "*"}:
            score = 3

    # Playwright text selector
    if "text selector" in lt:
        score = 6

    # Penalize if element lacks semantic attributes overall
    if not any([elem_id, data, role, elem.get("name"), elem.get("aria-label")]):
        score = max(1, score - 1)

    return max(1, min(10, int(score)))

def generate_locators_from_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    From extracted elements, generate two locator variants per element:
    - CSS Selector (id, data-test, or partial class)
    - XPath (text match or indexed)

    Stability rules:
    - Unique id -> High
    - Partial class match -> Medium
    - Indexed XPath -> Low
    - Text-based XPath -> Medium
    """
    # Build ID and name counts to determine uniqueness/duplicates
    id_counts: Dict[str, int] = {}
    name_counts: Dict[str, int] = {}
    for e in elements:
        eid = e.get("id")
        if eid:
            id_counts[eid] = id_counts.get(eid, 0) + 1
        ename = e.get("name")
        if ename:
            name_counts[ename] = name_counts.get(ename, 0) + 1

    # For XPath indexing, we need a soup; reconstruct minimal HTML to approximate
    # This is used only for counting position among tags.
    html_fragments = []
    for e in elements:
        attrs = []
        if e.get("id"):
            attrs.append(f"id=\"{e['id']}\"")
        if e.get("class"):
            attrs.append(f"class=\"{e['class']}\"")
        text = e.get("text", "")
        html_fragments.append(f"<{e.get('tag','div')} {' '.join(attrs)}>{text}</{e.get('tag','div')}>")
    soup = BeautifulSoup("\n".join(html_fragments), "lxml")

    locators: List[Dict[str, Any]] = []
    # Dynamic heuristics
    uuid_regex = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    long_digits_regex = re.compile(r"\d{5,}")
    timestamp_like_regex = re.compile(r"20\d{2}[\-_/]?\d{2}[\-_/]?\d{2}")

    def analyze_element_warnings(elem: Dict[str, Any]) -> Tuple[bool, bool, List[str]]:
        warnings: List[str] = []
        is_dynamic = False
        is_duplicate = False

        eid = elem.get("id") or ""
        ename = elem.get("name") or ""
        eclass = elem.get("class") or ""

        # Duplicate checks
        if eid and id_counts.get(eid, 0) > 1:
            is_duplicate = True
            warnings.append("Duplicate id detected")
        if ename and name_counts.get(ename, 0) > 1:
            is_duplicate = True
            warnings.append("Duplicate name detected")

        # Dynamic checks on id/class/name
        def looks_dynamic(value: str) -> bool:
            v = value.strip()
            if not v:
                return False
            if uuid_regex.match(v):
                return True
            if long_digits_regex.search(v):
                return True
            if timestamp_like_regex.search(v):
                return True
            # Many frameworks append hashes/indices: detect mixed alnum runs >= 6 incl digits
            if re.search(r"[A-Za-z]+\d+[A-Za-z\d]{3,}", v):
                return True
            return False

        if eid and looks_dynamic(eid):
            is_dynamic = True
            warnings.append("id appears dynamic (contains UUID/long digits/timestamp)")
        # Check each class token
        if eclass:
            for token in eclass.split():
                if looks_dynamic(token):
                    is_dynamic = True
                    warnings.append("class token appears dynamic")
                    break
        if ename and looks_dynamic(ename):
            is_dynamic = True
            warnings.append("name appears dynamic")

        return is_dynamic, is_duplicate, warnings

    for e in elements:
        custom_name = _guess_custom_name(e)
        dyn, dup, warn = analyze_element_warnings(e)

        css_info = _css_selector_for(e, id_counts)
        entry_css = {
            "custom_name": custom_name,
            "locator_type": css_info["type"],
            "locator_value": css_info["selector"],
            "stability": css_info["stability"],
            "automation_tool": _automation_tool_for(css_info["type"], css_info["selector"]),
            "dynamic": dyn,
            "duplicate": dup,
            "warnings": warn,
        }
        # Stability scoring
        css_score = _compute_stability_score(e, entry_css["locator_type"], entry_css["locator_value"], id_counts)
        entry_css["stability_score"] = css_score
        entry_css["stability"] = _label_from_score(css_score)
        entry_css.update(_generate_code_snippets(entry_css["locator_type"], entry_css["locator_value"], entry_css["automation_tool"]))
        locators.append(entry_css)

        xpath_info = _xpath_selector_for(e, soup)
        entry_xpath = {
            "custom_name": custom_name,
            "locator_type": xpath_info["type"],
            "locator_value": xpath_info["selector"],
            "automation_tool": _automation_tool_for(xpath_info["type"], xpath_info["selector"]),
            "dynamic": dyn,
            "duplicate": dup,
            "warnings": warn,
        }
        xpath_score = _compute_stability_score(e, entry_xpath["locator_type"], entry_xpath["locator_value"], id_counts)
        entry_xpath["stability_score"] = xpath_score
        entry_xpath["stability"] = _label_from_score(xpath_score)
        entry_xpath.update(_generate_code_snippets(entry_xpath["locator_type"], entry_xpath["locator_value"], entry_xpath["automation_tool"]))
        locators.append(entry_xpath)

        # Optional third: Playwright role/text-based selector
        pw = _playwright_role_selector_for(e)
        if pw:
            entry_pw = {
                "custom_name": custom_name,
                "locator_type": pw["type"],
                "locator_value": pw["selector"],
                "automation_tool": _automation_tool_for(pw["type"], pw["selector"]),
                "dynamic": dyn,
                "duplicate": dup,
                "warnings": warn,
            }
            pw_score = _compute_stability_score(e, entry_pw["locator_type"], entry_pw["locator_value"], id_counts)
            entry_pw["stability_score"] = pw_score
            entry_pw["stability"] = _label_from_score(pw_score)
            entry_pw.update(_generate_code_snippets(entry_pw["locator_type"], entry_pw["locator_value"], entry_pw["automation_tool"]))
            locators.append(entry_pw)

    return locators


def to_markdown_table(items: List[Dict[str, Any]]) -> str:
    """Render items as Markdown table. If locators were requested, show key locator fields.
    Otherwise, render element summaries.
    """
    if not items:
        return ""  # nothing to render

    # Determine if these are locator entries (presence of locator_type/value)
    is_locator = all(isinstance(x, dict) and ("locator_type" in x and "locator_value" in x) for x in items)

    if is_locator:
        headers = [
            "Custom Name",
            "Locator Type",
            "Locator Value",
            "Stability",
            "Automation Tool",
        ]
        rows = [
            [
                i.get("custom_name", ""),
                i.get("locator_type", ""),
                i.get("locator_value", ""),
                i.get("stability", i.get("stability_score", "")),
                i.get("automation_tool", ""),
            ]
            for i in items
        ]
    else:
        headers = [
            "Tag",
            "Id",
            "Name",
            "Class",
            "Text",
            "Role",
        ]
        rows = [
            [
                i.get("tag", ""),
                i.get("id", ""),
                i.get("name", ""),
                i.get("class", ""),
                (i.get("text", "") or "")[:120],
                i.get("role", ""),
            ]
            for i in items
        ]

    out_lines = []
    out_lines.append("| " + " | ".join(headers) + " |")
    out_lines.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
    for r in rows:
        out_lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out_lines) + "\n"


def compute_summary(locators: List[Dict[str, Any]], total_elements: int) -> Dict[str, Any]:
    """Compute overall summary statistics for generated locators."""
    locator_distribution: Dict[str, int] = {"css": 0, "xpath": 0, "role": 0}
    framework_split: Dict[str, int] = {"playwright": 0, "selenium": 0, "both": 0}
    stability_split: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for loc in locators:
        lt = (loc.get("locator_type", "").lower())
        if lt == "css selector":
            locator_distribution["css"] += 1
        elif lt == "xpath":
            locator_distribution["xpath"] += 1
        elif "role" in lt or "text selector" in lt:
            locator_distribution["role"] += 1

        tool = (loc.get("automation_tool", "").lower())
        if tool in ("playwright", "selenium", "both"):
            framework_split[tool] += 1

        stability = (loc.get("stability", loc.get("stability_score", "")).__str__()).lower()
        if "high" in stability:
            stability_split["high"] += 1
        elif "medium" in stability:
            stability_split["medium"] += 1
        elif "low" in stability:
            stability_split["low"] += 1

    return {
        "total_elements": int(total_elements),
        "locator_distribution": locator_distribution,
        "framework_split": framework_split,
        "stability": stability_split,
    }


def scan_dom(html_or_url: str, js_render: bool = False) -> List[Dict[str, Any]]:
    """
    Scan a web page (URL) or raw HTML string and return interactable elements.

    - If `html_or_url` looks like a URL, it fetches the page over HTTP.
    - If `js_render=True`, it will attempt to render with Playwright if available.
    - Otherwise, it treats the input as raw HTML content.
    """
    html: Optional[str] = None

    if _is_url(html_or_url):
        if js_render:
            html = _load_html_with_playwright(html_or_url)
        if not html:
            html = _load_html_from_url(html_or_url)
    else:
        # If a file path exists, load it; otherwise treat as raw HTML content
        if os.path.exists(html_or_url) and os.path.isfile(html_or_url):
            with open(html_or_url, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        else:
            html = html_or_url

    return extract_interactable_elements(html)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan a web page or HTML for interactable elements.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", type=str, help="Page URL to scan")
    group.add_argument("--file", type=str, help="Local HTML file to scan")
    group.add_argument("--html", type=str, help="Raw HTML content to scan")
    parser.add_argument("--js", action="store_true", help="Attempt JS render via Playwright (if installed)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--locators", action="store_true", help="Output CSS+XPath locator variants instead of raw elements")
    parser.add_argument("--export-json", type=str, help="Write results to JSON file")
    parser.add_argument("--export-md", type=str, help="Write results to Markdown table file")
    parser.add_argument("--export-summary", type=str, help="Write summary JSON to file (only with --locators)")

    args = parser.parse_args()

    target = args.url or args.file or args.html
    try:
        elements = scan_dom(target, js_render=args.js)
        if args.locators:
            results = generate_locators_from_elements(elements)
        else:
            results = elements

        # Optional exports
        if args.export_json:
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2 if args.pretty else None, ensure_ascii=False)
            print(f"Wrote JSON to {args.export_json}")

        if args.export_md:
            md = to_markdown_table(results)
            with open(args.export_md, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Wrote Markdown to {args.export_md}")

        # Summary (only meaningful for locator results)
        if args.locators:
            summary = compute_summary(results, total_elements=len(elements))
            if args.export_summary:
                with open(args.export_summary, "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print(f"Wrote Summary to {args.export_summary}")
            # Also print summary to stdout after main JSON
            print(json.dumps({"summary": summary}, indent=2, ensure_ascii=False))

        # Print to stdout as JSON for CLI pipelines
        if args.pretty:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(results, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()


