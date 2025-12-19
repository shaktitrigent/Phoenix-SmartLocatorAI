"""Tests for core API functionality"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from phoenix_smartlocatorai.core import generate_locators_from_dom


def test_generate_locators_from_html_file():
    """Test generating locators from an HTML file"""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head><title>Test Page</title></head>
        <body>
            <button id="submit-btn" class="btn-primary">Submit</button>
            <input type="text" name="username" id="username-input" />
            <a href="/home" class="nav-link">Home</a>
        </body>
    </html>
    """
    
    with TemporaryDirectory() as tmpdir:
        # Write HTML file
        html_file = Path(tmpdir) / "test.html"
        html_file.write_text(html_content, encoding="utf-8")
        
        # Generate locators
        result = generate_locators_from_dom(
            input_html_or_url=str(html_file),
            frameworks=["Playwright", "Selenium"],
            output_dir=tmpdir,
            class_name="TestPage",
        )
        
        # Check that files were generated
        assert "locators_json" in result
        assert Path(result["locators_json"]).exists()
        
        # Check locators.json content
        with open(result["locators_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "summary" in data
        assert "locators" in data
        assert len(data["locators"]) > 0
        
        # Check that Page Object files were generated
        assert "playwright_pom" in result
        assert "selenium_pom" in result
        assert Path(result["playwright_pom"]).exists()
        assert Path(result["selenium_pom"]).exists()


def test_generate_locators_from_html_string():
    """Test generating locators from HTML string"""
    html_content = """
    <html>
        <body>
            <button id="submit-btn">Submit</button>
            <input type="text" name="username" />
        </body>
    </html>
    """
    
    with TemporaryDirectory() as tmpdir:
        result = generate_locators_from_dom(
            input_html_or_url=html_content,
            frameworks=["Selenium"],
            output_dir=tmpdir,
            class_name="TestPage",
        )
        
        assert "locators_json" in result
        assert Path(result["locators_json"]).exists()
        
        # When only one framework, page.py should be generated
        assert "page_py" in result
        assert Path(result["page_py"]).exists()


def test_min_stability_filter():
    """Test filtering by minimum stability"""
    html_content = """
    <html>
        <body>
            <button id="high-stability-btn">High</button>
            <button class="medium-stability-btn">Medium</button>
            <div>Low stability element</div>
        </body>
    </html>
    """
    
    with TemporaryDirectory() as tmpdir:
        # Generate with High stability filter
        result = generate_locators_from_dom(
            input_html_or_url=html_content,
            frameworks=["Playwright"],
            output_dir=tmpdir,
            min_stability="High",
        )
        
        with open(result["locators_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # All locators should be High stability
        for locator in data["locators"]:
            assert locator.get("stability") == "High"


def test_single_framework_generates_page_py():
    """Test that single framework generates page.py"""
    html_content = "<html><body><button id='test'>Test</button></body></html>"
    
    with TemporaryDirectory() as tmpdir:
        result = generate_locators_from_dom(
            input_html_or_url=html_content,
            frameworks=["Playwright"],
            output_dir=tmpdir,
        )
        
        assert "page_py" in result
        assert Path(result["page_py"]).exists()
        
        # Check that page.py contains Playwright code
        content = Path(result["page_py"]).read_text(encoding="utf-8")
        assert "from playwright.sync_api import Page" in content or "page.locator" in content


