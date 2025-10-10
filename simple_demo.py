"""
Simple Demo - Just run this to see locator generation in action
"""
from locator_generator import LocatorGenerator


def main():
    """Main demo function"""
    
    print("🎯 Simple Locator Generator Demo")
    print("=" * 60)
    print("This demo shows how to generate locators for web elements")
    print("You can use either DOM content or URLs!")
    print("=" * 60)
    
    # Usage examples
    print("\n💡 USAGE EXAMPLES:")
    print("-" * 40)
    print("1. With DOM content:")
    print("   generator.generate_locators(html_string, '#my-button')")
    print("2. With URL:")
    print("   generator.generate_locators('https://example.com', '#my-button')")
    print("3. Auto-detect (works with both DOM and URL):")
    print("   generator.generate_locators(html_or_url)")
    print("-" * 40)
    
    # Sample HTML with various elements
    sample_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>E-commerce Login Page</title>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>MyStore</h1>
                <nav>
                    <a href="/home" id="home-link">Home</a>
                    <a href="/products" class="nav-link">Products</a>
                </nav>
            </header>
            
            <main>
                <div class="login-section">
                    <h2>Sign In</h2>
                    <form id="login-form" class="form-container">
                        <div class="form-group">
                            <label for="email">Email:</label>
                            <input 
                                type="email" 
                                id="email-input" 
                                name="email" 
                                placeholder="Enter your email"
                                data-test="email-field"
                                required
                            >
                        </div>
                        
                        <div class="form-group">
                            <label for="password">Password:</label>
                            <input 
                                type="password" 
                                id="password-input" 
                                name="password" 
                                placeholder="Enter your password"
                                data-test="password-field"
                                required
                            >
                        </div>
                        
                        <div class="form-actions">
                            <button 
                                id="login-button" 
                                type="submit" 
                                class="btn btn-primary btn-large"
                                data-test="login-submit"
                            >
                                Sign In
                            </button>
                            
                            <button 
                                type="button" 
                                class="btn btn-secondary"
                                data-test="forgot-password"
                                onclick="showForgotPassword()"
                            >
                                Forgot Password?
                            </button>
                        </div>
                    </form>
                    
                    <div class="signup-link">
                        <p>Don't have an account? 
                            <a href="/register" id="signup-link" data-testid="register-link">
                                Create one here
                            </a>
                        </p>
                    </div>
                </div>
            </main>
            
            <footer>
                <p>&copy; 2024 MyStore. All rights reserved.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Initialize the generator
    generator = LocatorGenerator()
    
    # Demo 1: Login Button
    print("\n📍 DEMO 1: Login Button")
    print("-" * 40)
    print("Target: Login button with ID 'login-button'")
    
    locators = generator.generate_locators(sample_html, "#login-button")
    
    print(f"\n✅ Generated {len(locators)} locators:")
    for i, locator in enumerate(locators, 1):
        print(f"\n{i}. {locator['type']}")
        print(f"   Selector: {locator['selector']}")
        print(f"   Stability: {locator['stability']}")
        print(f"   Explanation: {locator['explanation']}")
    
    # Demo 2: Email Input Field
    print("\n\n📍 DEMO 2: Email Input Field")
    print("-" * 40)
    print("Target: Email input field")
    
    locators = generator.generate_locators(sample_html, "input[name='email']")
    
    print(f"\n✅ Generated {len(locators)} locators:")
    for i, locator in enumerate(locators, 1):
        print(f"\n{i}. {locator['type']}")
        print(f"   Selector: {locator['selector']}")
        print(f"   Stability: {locator['stability']}")
        print(f"   Explanation: {locator['explanation']}")
    
    # Demo 3: Sign Up Link
    print("\n\n📍 DEMO 3: Sign Up Link")
    print("-" * 40)
    print("Target: Sign up link")
    
    locators = generator.generate_locators(sample_html, "#signup-link")
    
    print(f"\n✅ Generated {len(locators)} locators:")
    for i, locator in enumerate(locators, 1):
        print(f"\n{i}. {locator['type']}")
        print(f"   Selector: {locator['selector']}")
        print(f"   Stability: {locator['stability']}")
        print(f"   Explanation: {locator['explanation']}")
    
    # Demo 4: Auto-detect first interactive element
    print("\n\n📍 DEMO 4: Auto-detect First Interactive Element")
    print("-" * 40)
    print("Target: First interactive element found automatically")
    
    locators = generator.generate_locators(sample_html)
    
    print(f"\n✅ Generated {len(locators)} locators:")
    for i, locator in enumerate(locators, 1):
        print(f"\n{i}. {locator['type']}")
        print(f"   Selector: {locator['selector']}")
        print(f"   Stability: {locator['stability']}")
        print(f"   Explanation: {locator['explanation']}")
    
    # Show element info for the auto-detected elements
    elements_info = generator.get_element_info(sample_html)
    print(f"\n📋 Auto-detected elements info:")
    if isinstance(elements_info, list):
        for i, element_info in enumerate(elements_info):
            print(f"   Element {i}: {element_info['tag_name']} - {element_info['text_content']}")
            print(f"   Attributes: {element_info['attributes']}")
    else:
        print(f"   Tag: {element_info['tag_name']}")
        print(f"   Text: {element_info['text_content']}")
        print(f"   Attributes: {element_info['attributes']}")
    
    # Demo 5: URL-based locator generation (example with a real website)
    print("\n\n📍 DEMO 5: URL-based Locator Generation")
    print("-" * 40)
    print("Target: Generate locators from a live website")
    print("Note: This will fetch HTML from a real URL")
    
    try:
        # Example with a simple, reliable website
        test_url = "https://httpbin.org/html"
        print(f"Fetching from: {test_url}")
        
        locators = generator.generate_locators(test_url, "h1")
        
        print(f"\n✅ Generated {len(locators)} locators:")
        for i, locator in enumerate(locators, 1):
            print(f"\n{i}. {locator['type']}")
            print(f"   Selector: {locator['selector']}")
            print(f"   Stability: {locator['stability']}")
            print(f"   Explanation: {locator['explanation']}")
            
    except Exception as e:
        print(f"❌ URL demo failed (this is expected in some environments): {e}")
        print("💡 You can still use the generator with any URL that's accessible from your network")
    
    print("\n\n🎉 Demo completed!")
    print("=" * 60)
    print("This simple generator can:")
    print("• Parse HTML and find elements")
    print("• Generate multiple locator types")
    print("• Rank locators by stability")
    print("• Auto-detect interactive elements")
    print("• Fetch HTML from URLs automatically")
    print("• Work with both DOM content and live websites")
    print("=" * 60)


if __name__ == "__main__":
    main()
