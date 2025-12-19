"""
Example usage of Phoenix Smart Locator AI package
"""

from phoenix_smartlocatorai import generate_locators_from_dom

# Example 1: Generate locators from HTML string
html = """
<html>
    <head><title>Test Page</title></head>
    <body>
        <button id="submit-btn" class="btn-primary">Submit</button>
        <input type="text" name="username" id="username-input" />
        <a href="/home" class="nav-link">Home</a>
    </body>
</html>
"""

print("Generating locators from HTML...")
result = generate_locators_from_dom(
    input_html_or_url=html,
    frameworks=["Playwright", "Selenium"],
    output_dir="./example_output",
    class_name="TestPage",
)

print(f"\nGenerated files:")
for key, path in result.items():
    print(f"  - {key}: {path}")

print("\nDone! Check the example_output directory for generated files.")


