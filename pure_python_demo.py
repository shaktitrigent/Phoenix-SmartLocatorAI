#!/usr/bin/env python3
"""
Pure Python Enhanced Locator Generator Demo
NO AI dependencies required - uses only standard Python libraries
"""

from locator_generator import LocatorGenerator
import json

def demo_pure_python_features():
    """Demo the enhanced locator generator using ONLY pure Python"""
    
    print("🐍 PURE PYTHON ENHANCED LOCATOR GENERATOR")
    print("=" * 60)
    print("✅ NO AI dependencies required!")
    print("✅ Uses only: beautifulsoup4, requests, lxml, re, json")
    print("=" * 60)
    
    # Sample HTML
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
    
    # Initialize the enhanced locator generator (NO AI dependencies)
    generator = LocatorGenerator()
    
    print("📍 PURE PYTHON FEATURE 1: ALL Web Elements Detection")
    print("-" * 50)
    
    # Generate locators for ALL elements using pure Python
    all_locators = generator.generate_locators(sample_html)
    print(f"✅ Found {len(all_locators)} locators using pure Python")
    
    # Group by element type
    element_types = {}
    for locator in all_locators:
        tag_name = locator.get('tag_name', 'unknown')
        if tag_name not in element_types:
            element_types[tag_name] = 0
        element_types[tag_name] += 1
    
    print(f"✅ Element types found: {', '.join(element_types.keys())}")
    
    print("\n📍 PURE PYTHON FEATURE 2: Intelligent Element Naming")
    print("-" * 50)
    
    # Group locators by element name (pure Python logic)
    element_groups = {}
    for locator in all_locators:
        element_name = locator.get('element_name', f"element_{locator['element_index']}")
        if element_name not in element_groups:
            element_groups[element_name] = []
        element_groups[element_name].append(locator)
    
    print(f"✅ Found {len(element_groups)} unique elements with intelligent names:")
    for i, (element_name, locators) in enumerate(list(element_groups.items())[:5]):
        print(f"   {i+1}. {element_name} ({len(locators)} locators)")
    
    print("\n📍 PURE PYTHON FEATURE 3: Priority-Based Suggestions")
    print("-" * 50)
    
    # Show examples of priority suggestions (pure Python logic)
    print("💡 Priority Suggestions Examples (Pure Python Logic):")
    for i, (element_name, locators) in enumerate(list(element_groups.items())[:3]):
        print(f"\n  {i+1}. Element: {element_name}")
        for j, locator in enumerate(locators[:2]):
            print(f"     Locator {j+1} ({locator['type']}): {locator['selector']}")
            if 'suggestions' in locator:
                print(f"       🔴 High: {locator['suggestions']['High']}")
                print(f"       🟡 Medium: {locator['suggestions']['Medium']}")
                print(f"       🟢 Low: {locator['suggestions']['Low']}")
    
    print("\n📍 PURE PYTHON FEATURE 4: Export with Enhanced Data")
    print("-" * 50)
    
    # Export to JSON (pure Python)
    export_data = {
        'total_locators': len(all_locators),
        'total_elements': len(element_groups),
        'element_types': element_types,
        'elements': {}
    }
    
    for element_name, locators in element_groups.items():
        export_data['elements'][element_name] = {
            'locator_count': len(locators),
            'locators': locators
        }
    
    with open('pure_python_locators_export.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print("✅ Pure Python locators exported to: pure_python_locators_export.json")
    
    print("\n🎉 PURE PYTHON DEMO COMPLETE!")
    print("=" * 60)
    print("🚀 PURE PYTHON FEATURES DEMONSTRATED:")
    print("• ✅ ALL web elements detection (pure Python)")
    print("• ✅ Intelligent element naming (pure Python)")
    print("• ✅ Priority-based suggestions (pure Python)")
    print("• ✅ Enhanced export (pure Python)")
    print("• ✅ NO AI dependencies required!")
    print("• ✅ Same high-quality results!")

if __name__ == "__main__":
    demo_pure_python_features()
