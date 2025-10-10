#!/usr/bin/env python3
"""
Gemini-Only Locator Generator Demo
Uses only Google Gemini 2.5 Flash for AI enhancement
"""

import os
from gemini_enhanced_locator_generator import GeminiEnhancedLocatorGenerator

def print_setup_instructions():
    """Print setup instructions for Gemini"""
    print("🤖 GEMINI SETUP INSTRUCTIONS")
    print("=" * 50)
    print("1. Get Gemini API Key:")
    print("   • Visit: https://makersuite.google.com/app/apikey")
    print("   • Create a new API key")
    print("")
    print("2. Set Environment Variable:")
    print("   # For Windows (PowerShell)")
    print("   $env:GOOGLE_API_KEY='your_key_here'")
    print("")
    print("   # For Linux/Mac")
    print("   export GOOGLE_API_KEY='your_key_here'")
    print("")
    print("3. Install Dependencies:")
    print("   pip install google-generativeai")
    print("")
    print("4. Run Demo:")
    print("   python gemini_demo.py")
    print("=" * 50)

def demo_gemini_locator_generator():
    """Demo the Gemini-enhanced locator generator"""
    
    print("🤖 GEMINI-ENHANCED LOCATOR GENERATOR DEMO")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ No Gemini API key found!")
        print_setup_instructions()
        print("\nRunning demo without AI features...")
        
        # Run basic demo without AI
        from locator_generator import LocatorGenerator
        generator = LocatorGenerator()
        
        sample_html = """
        <html>
            <body>
                <div class="container">
                    <h1>Test Page</h1>
                    <button id="test-btn" class="btn btn-primary" data-test="test-button">Click Me</button>
                    <input type="text" name="username" placeholder="Username" data-test="username-input">
                </div>
            </body>
        </html>
        """
        
        locators = generator.generate_locators(sample_html)
        print(f"✅ Generated {len(locators)} locators (basic mode)")
        
        # Show some examples
        for i, locator in enumerate(locators[:3]):
            print(f"  {i+1}. {locator['type']}: {locator['selector']}")
        
        return
    
    print("✅ Gemini API key found!")
    
    # Sample HTML with various elements
    sample_html = """
    <html>
        <head><title>E-commerce Product Page</title></head>
        <body>
            <div class="container">
                <h1>Premium Wireless Headphones</h1>
                <nav class="breadcrumb">
                    <a href="/">Home</a> > <a href="/electronics">Electronics</a>
                </nav>
                
                <form id="login-form" class="auth-form">
                    <input type="text" name="username" placeholder="Username" data-test="username-input" class="form-input">
                    <input type="password" name="password" placeholder="Password" data-test="password-input" class="form-input">
                    <button id="login-btn" class="btn btn-primary" data-test="login-button" type="submit">
                        Login
                    </button>
                </form>
                
                <div class="product-info">
                    <img src="/images/headphones.jpg" alt="Premium Headphones" class="product-image">
                    <p class="description">High-quality wireless headphones with noise cancellation.</p>
                    <button id="add-to-cart" class="btn btn-primary" data-test="add-to-cart-btn">Add to Cart</button>
                    <button id="buy-now" class="btn btn-secondary" data-test="buy-now-btn">Buy Now</button>
                    <button id="wishlist" class="btn btn-outline" data-test="wishlist-btn">Add to Wishlist</button>
                </div>
                
                <div class="footer">
                    <p>&copy; 2024 TechStore. All rights reserved.</p>
                    <a href="/contact" class="contact-link">Contact Us</a>
                </div>
            </div>
        </body>
    </html>
    """
    
    # Initialize Gemini-enhanced generator
    generator = GeminiEnhancedLocatorGenerator()
    
    print("🚀 Generating Gemini-enhanced locators...")
    
    # Generate enhanced locators
    results = generator.generate_gemini_enhanced_locators(sample_html)
    
    print(f"✅ Generated {results['total_locators']} locators")
    print(f"✅ AI Provider: {results['ai_provider']}")
    print(f"✅ Model: {results['model']}")
    
    # Display AI analysis
    analysis = results['ai_analysis']
    print(f"\n🧠 AI Analysis:")
    print(f"  • Page Type: {analysis.get('page_type', 'Unknown')}")
    print(f"  • Quality Score: {analysis.get('element_quality_score', 'N/A')}")
    print(f"  • Best Strategies: {analysis.get('best_strategies', [])}")
    print(f"  • Maintenance Risk: {analysis.get('maintenance_risk_score', 'N/A')}")
    
    # Display recommendations
    print(f"\n💡 AI Recommendations ({len(results['ai_recommendations'])} elements):")
    for i, rec in enumerate(results['ai_recommendations'][:3]):
        print(f"  {i+1}. Element: {rec.get('element_name', 'Unknown')}")
        print(f"     Priority: {rec.get('improvement_priority', 'N/A')}")
        suggestions = rec.get('specific_suggestions', [])
        if suggestions:
            print(f"     Top Suggestion: {suggestions[0][:80]}...")
    
    # Display code generation
    code = results['ai_code']
    print(f"\n💻 AI-Generated Code:")
    print(f"  • Selenium: {len(code.get('selenium', ''))} characters")
    print(f"  • Playwright: {len(code.get('playwright', ''))} characters")
    print(f"  • Cypress: {len(code.get('cypress', ''))} characters")
    
    # Export results
    json_file = generator.export_gemini_enhanced_results(results, 'json')
    md_file = generator.export_gemini_enhanced_results(results, 'markdown')
    
    print(f"\n📄 Reports saved:")
    print(f"  • JSON: {json_file}")
    print(f"  • Markdown: {md_file}")
    
    print(f"\n🎉 Gemini-Enhanced Demo Complete!")
    print("=" * 60)
    print("🚀 FEATURES DEMONSTRATED:")
    print("• ✅ ALL web elements detection")
    print("• ✅ Intelligent element naming")
    print("• ✅ Priority-based suggestions")
    print("• ✅ Gemini AI analysis")
    print("• ✅ AI-powered recommendations")
    print("• ✅ Production-ready code generation")
    print("• ✅ Comprehensive reporting")

if __name__ == "__main__":
    demo_gemini_locator_generator()
