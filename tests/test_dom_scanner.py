"""Tests for DOM scanner functionality"""

import json
from pathlib import Path

from phoenix_smartlocatorai.dom_scanner import (
    scan_dom,
    generate_locators_from_elements,
    compute_summary,
)


def test_scan_dom_from_html():
    """Test scanning DOM from HTML string"""
    html = """
    <html>
        <body>
            <button id="submit-btn" class="btn-primary">Submit</button>
            <input type="text" name="username" id="username-input" />
            <a href="/home" class="nav-link">Home</a>
        </body>
    </html>
    """
    
    elements = scan_dom(html, js_render=False)
    
    assert len(elements) >= 3
    assert any(e.get("tag") == "button" and e.get("id") == "submit-btn" for e in elements)
    assert any(e.get("tag") == "input" and e.get("name") == "username" for e in elements)
    assert any(e.get("tag") == "a" and e.get("href") == "/home" for e in elements)


def test_generate_locators():
    """Test locator generation from elements"""
    elements = [
        {
            "tag": "button",
            "id": "submit-btn",
            "class": "btn-primary",
            "text": "Submit",
        },
        {
            "tag": "input",
            "id": "username-input",
            "name": "username",
            "type": "text",
        },
    ]
    
    locators = generate_locators_from_elements(elements)
    
    assert len(locators) > 0
    
    # Check that we have locators for the button
    button_locators = [l for l in locators if "submit" in l.get("custom_name", "").lower()]
    assert len(button_locators) > 0
    
    # Check locator structure
    for loc in locators:
        assert "custom_name" in loc
        assert "locator_type" in loc
        assert "locator_value" in loc
        assert "stability" in loc
        assert "automation_tool" in loc


def test_compute_summary():
    """Test summary computation"""
    locators = [
        {
            "custom_name": "SubmitButton",
            "locator_type": "CSS Selector",
            "locator_value": "#submit-btn",
            "stability": "High",
            "automation_tool": "Both",
        },
        {
            "custom_name": "UsernameInput",
            "locator_type": "XPath",
            "locator_value": "//input[@name='username']",
            "stability": "Medium",
            "automation_tool": "Selenium",
        },
    ]
    
    summary = compute_summary(locators, total_elements=2)
    
    assert "total_elements" in summary
    assert "total_locators" in summary
    assert "locator_distribution" in summary
    assert "framework_split" in summary
    assert "stability" in summary
    
    assert summary["total_elements"] == 2
    assert summary["total_locators"] == 2
    assert summary["stability"]["high"] >= 1
    assert summary["stability"]["medium"] >= 1


def test_locator_stability_scoring():
    """Test that stability scoring works correctly"""
    elements = [
        {"tag": "button", "id": "unique-id-123"},  # Should be High
        {"tag": "button", "class": "btn"},  # Should be Medium
        {"tag": "div", "text": "Some text"},  # Should be Low
    ]
    
    locators = generate_locators_from_elements(elements)
    
    # Find locators with unique IDs (should be High stability)
    high_stability = [l for l in locators if l.get("stability") == "High" and "unique-id" in l.get("locator_value", "")]
    assert len(high_stability) > 0


