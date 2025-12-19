#!/usr/bin/env python3
"""
Page Object Exporter

Takes generated locator JSON (from dom_scanner --locators) and exports Page Object
classes for Playwright or Selenium.

CLI usage:
  python page_object_exporter.py --input locators.json --framework playwright --class ProductPage --output ProductPage.py
  python page_object_exporter.py --input locators.json --framework selenium --class ProductPage --output ProductPage.py
"""

import argparse
import json
import re
from typing import Dict, List, Tuple


def _to_snake_case(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name or "")
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = name.lower().strip("_")
    if not name:
        name = "element"
    if name[0].isdigit():
        name = f"e_{name}"
    return name


def _prefer_order_playwright(locator_type: str) -> int:
    order = {
        "Role Selector": 0,
        "CSS Selector": 1,
        "Text Selector": 2,
        "XPath": 3,
    }
    return order.get(locator_type, 9)


def _prefer_order_selenium(locator_type: str) -> int:
    order = {
        "CSS Selector": 0,
        "XPath": 1,
    }
    return order.get(locator_type, 9)


def _select_best_per_name(locators: List[Dict], framework: str) -> Dict[str, Dict]:
    """Select the best locator per custom_name for the target framework.
    Preference: highest stability_score, then by framework-specific type order.
    """
    best: Dict[str, Dict] = {}
    for loc in locators:
        name = loc.get("custom_name") or "Element"
        # Filter by automation_tool compatibility
        tool = loc.get("automation_tool", "Both")
        if framework == "playwright" and tool not in ("Playwright", "Both"):
            continue
        if framework == "selenium" and tool not in ("Selenium", "Both"):
            continue

        curr = best.get(name)
        if not curr:
            best[name] = loc
            continue

        curr_score = int(curr.get("stability_score", 0))
        new_score = int(loc.get("stability_score", 0))
        if new_score > curr_score:
            best[name] = loc
            continue
        if new_score == curr_score:
            if framework == "playwright":
                if _prefer_order_playwright(loc.get("locator_type", "")) < _prefer_order_playwright(curr.get("locator_type", "")):
                    best[name] = loc
            else:
                if _prefer_order_selenium(loc.get("locator_type", "")) < _prefer_order_selenium(curr.get("locator_type", "")):
                    best[name] = loc

    return best


def generate_playwright_pom(locators: List[Dict], class_name: str = "ProductPage") -> str:
    best = _select_best_per_name(locators, framework="playwright")
    lines: List[str] = []
    lines.append("from playwright.sync_api import Page\n")
    lines.append(f"\n\nclass {class_name}:")
    lines.append("\n    def __init__(self, page: Page):")
    lines.append("        self.page = page")

    for custom_name, loc in sorted(best.items()):
        var = _to_snake_case(custom_name)
        lt = loc.get("locator_type", "")
        lv = loc.get("locator_value", "")
        if lt == "Role Selector" or lt == "Text Selector":
            # locator_value already 'page.getByRole(...)' or 'page.getByText(...)'
            # Use as property call-time; create a Locator via page.locator when possible
            # For simplicity, use evaluate from code snippet without .click()
            # Convert to a locator handle:
            # e.g., page.getByRole('button', { name: 'X' })
            expr = lv.replace(".click()", "")
            lines.append(f"        self.{var} = {expr}")
        elif lt == "CSS Selector":
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = page.locator(\"{safe}\")")
        elif lt == "XPath":
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = page.locator(\"xpath={safe}\")")
        else:
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = page.locator(\"{safe}\")")

    return "\n".join(lines) + "\n"


def generate_selenium_pom(locators: List[Dict], class_name: str = "ProductPage") -> str:
    best = _select_best_per_name(locators, framework="selenium")
    lines: List[str] = []
    lines.append("from selenium.webdriver.common.by import By\n")
    lines.append(f"\n\nclass {class_name}:")
    lines.append("\n    def __init__(self, driver):")
    lines.append("        self.driver = driver")

    for custom_name, loc in sorted(best.items()):
        var = _to_snake_case(custom_name)
        lt = loc.get("locator_type", "")
        lv = loc.get("locator_value", "")
        if lt == "CSS Selector":
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = driver.find_element(By.CSS_SELECTOR, \"{safe}\")")
        elif lt == "XPath":
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = driver.find_element(By.XPATH, \"{safe}\")")
        else:
            # Fallback to CSS
            safe = lv.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f"        self.{var} = driver.find_element(By.CSS_SELECTOR, \"{safe}\")")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Page Object classes from locator JSON")
    parser.add_argument("--input", required=True, help="Path to locator JSON file")
    parser.add_argument("--framework", required=True, choices=["playwright", "selenium"], help="Target framework")
    parser.add_argument("--class", dest="class_name", default="ProductPage", help="Class name for the Page Object")
    parser.add_argument("--output", required=True, help="Output .py file path")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        locators: List[Dict] = json.load(f)

    if args.framework == "playwright":
        content = generate_playwright_pom(locators, class_name=args.class_name)
    else:
        content = generate_selenium_pom(locators, class_name=args.class_name)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Wrote Page Object to {args.output}")


if __name__ == "__main__":
    main()


