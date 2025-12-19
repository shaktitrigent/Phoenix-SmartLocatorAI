#!/usr/bin/env python3
"""
CLI tool for Phoenix Smart Locator AI
"""

import argparse
import sys
from pathlib import Path

from phoenix_smartlocatorai.core import generate_locators_from_dom


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phoenix Smart Locator AI - Generate locators from HTML or URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  phoenix-locgen --input page.html --frameworks Playwright,Selenium
  phoenix-locgen --input https://example.com --frameworks Playwright --output ./out
  phoenix-locgen --input page.html --frameworks Selenium --min-stability High
        """,
    )
    
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input HTML file path or URL to scan",
    )
    
    parser.add_argument(
        "--frameworks",
        "-f",
        default="Playwright,Selenium",
        help="Comma-separated list of frameworks: Playwright, Selenium (default: Playwright,Selenium)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory for generated files (default: current directory)",
    )
    
    parser.add_argument(
        "--class-name",
        "-c",
        default="Page",
        help="Name for the Page Object class (default: Page)",
    )
    
    parser.add_argument(
        "--min-stability",
        "-s",
        choices=["High", "Medium", "Low"],
        help="Filter locators by minimum stability level",
    )
    
    parser.add_argument(
        "--js",
        action="store_true",
        help="Use Playwright to render JavaScript (for URL inputs)",
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate locators in real browser (URL inputs only, requires Playwright)",
    )
    
    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Enable Gemini AI enrichment (requires GOOGLE_API_KEY)",
    )
    
    # Auth options for validation
    auth_group = parser.add_argument_group("authentication options (for --validate)")
    auth_group.add_argument("--auth-storage-state", help="Playwright storage state JSON path")
    auth_group.add_argument("--auth-url", help="Login URL for simple auth flow")
    auth_group.add_argument("--auth-user", help="Username for simple auth flow")
    auth_group.add_argument("--auth-pass", help="Password for simple auth flow")
    auth_group.add_argument("--user-selector", help="Selector for username field")
    auth_group.add_argument("--pass-selector", help="Selector for password field")
    auth_group.add_argument("--submit-selector", help="Selector for login submit button")
    auth_group.add_argument("--auth-wait-selector", help="Selector to wait for post-login")
    auth_group.add_argument("--auth-wait-url-contains", help="Substring of URL to wait for after login")
    
    args = parser.parse_args()
    
    # Parse frameworks
    frameworks = [f.strip() for f in args.frameworks.split(",")]
    valid_frameworks = {"playwright", "selenium"}
    frameworks = [f for f in frameworks if f.lower() in valid_frameworks]
    
    if not frameworks:
        print("Error: No valid frameworks specified. Use Playwright and/or Selenium.", file=sys.stderr)
        sys.exit(1)
    
    # Prepare auth options
    auth_opts = {}
    if args.validate:
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
    
    try:
        result_paths = generate_locators_from_dom(
            input_html_or_url=args.input,
            frameworks=frameworks,
            output_dir=args.output,
            class_name=args.class_name,
            min_stability=args.min_stability,
            use_js=args.js,
            validate=args.validate,
            auth_opts=auth_opts if args.validate else None,
            use_gemini=args.gemini,
        )
        
        print("✅ Successfully generated locators!")
        print(f"\nGenerated files:")
        for key, path in result_paths.items():
            print(f"  • {key}: {path}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


