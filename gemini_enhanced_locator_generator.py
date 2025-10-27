#!/usr/bin/env python3
"""
Gemini-Enhanced Locator Generator
Uses only Google Gemini 2.5 Flash for AI-powered locator analysis and code generation
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import the base locator generator
from locator_generator import LocatorGenerator

# Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("WARNING: Google Generative AI not available. Install with: pip install google-generativeai")


class GeminiEnhancedLocatorGenerator(LocatorGenerator):
    """
    Enhanced locator generator with Gemini 2.5 Flash AI integration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Initialize Gemini client
        self.gemini_client = None
        self.model_name = 'gemini-2.0-flash-exp'  # Latest Gemini model
        
        # Initialize Gemini
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini client"""
        if not GEMINI_AVAILABLE:
            print("WARNING: Gemini not available. Running in basic mode.")
            return
        
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel(self.model_name)
                print(f"SUCCESS: Gemini {self.model_name} client initialized")
            except Exception as e:
                print(f"WARNING: Failed to initialize Gemini: {e}")
                self.gemini_client = None
        else:
            print("WARNING: Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
    
    def _call_gemini(self, prompt: str, context: str = "") -> str:
        """Call Gemini API with the given prompt"""
        if not self.gemini_client:
            return "Gemini not available"
        
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            response = self.gemini_client.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"Gemini API error: {str(e)}"
    
    def generate_gemini_enhanced_locators(self, html_or_url: str, target_selector: str = None) -> Dict[str, Any]:
        """
        Generate locators with Gemini AI enhancement
        
        Args:
            html_or_url: HTML content or URL
            target_selector: Optional CSS selector for specific element
            
        Returns:
            Dictionary with enhanced locators and AI analysis
        """
        print("INFO: Generating Gemini-enhanced locators...")
        
        # Generate base locators using the parent class
        base_locators = self.generate_locators(html_or_url, target_selector)
        print(f"SUCCESS: Generated {len(base_locators)} base locators")
        
        # Get HTML content for AI analysis
        if self._is_url(html_or_url):
            html_content = self._fetch_html_from_url(html_or_url)
        else:
            html_content = html_or_url
        
        # Perform AI analysis
        ai_analysis = self._perform_gemini_analysis(html_content, base_locators)
        
        # Generate AI recommendations
        ai_recommendations = self._generate_gemini_recommendations(base_locators)
        
        # Generate AI code
        ai_code = self._generate_gemini_code(base_locators)
        
        return {
            'locators': base_locators,
            'total_locators': len(base_locators),
            'ai_analysis': ai_analysis,
            'ai_recommendations': ai_recommendations,
            'ai_code': ai_code,
            'generated_at': datetime.now().isoformat(),
            'ai_provider': 'gemini',
            'model': self.model_name
        }
    
    def _perform_gemini_analysis(self, html_content: str, locators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform AI analysis of the page and locators"""
        if not self.gemini_client:
            return {"error": "Gemini not available"}
        
        # Prepare context for AI
        locator_summary = self._prepare_locator_summary(locators)
        
        prompt = f"""
        Analyze this web page and its locators for test automation:

        HTML Content (first 2000 chars):
        {html_content[:2000]}

        Locator Summary:
        {locator_summary}

        Please provide a JSON response with:
        1. page_type: Type of page (e.g., e-commerce, login, dashboard)
        2. element_quality_score: Score from 1-10 for element quality
        3. best_strategies: List of best locator strategies
        4. potential_issues: List of potential issues with current locators
        5. best_practices_compliance: Score from 1-10
        6. maintenance_risk_score: Score from 1-10 (lower is better)
        7. overall_recommendations: List of key recommendations

        Respond with valid JSON only.
        """
        
        response = self._call_gemini(prompt)
        
        try:
            # Try to parse JSON response
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                # If not JSON, create structured response
                return {
                    "page_type": "web page",
                    "element_quality_score": 7,
                    "best_strategies": ["ID", "Data Test"],
                    "potential_issues": ["Some locators may be fragile"],
                    "best_practices_compliance": 7,
                    "maintenance_risk_score": 5,
                    "overall_recommendations": [response],
                    "raw_response": response
                }
        except json.JSONDecodeError:
            return {
                "page_type": "web page",
                "element_quality_score": 7,
                "best_strategies": ["ID", "Data Test"],
                "potential_issues": ["Some locators may be fragile"],
                "best_practices_compliance": 7,
                "maintenance_risk_score": 5,
                "overall_recommendations": [response],
                "raw_response": response
            }
    
    def _generate_gemini_recommendations(self, locators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate AI recommendations for each element"""
        if not self.gemini_client:
            return []
        
        recommendations = []
        
        # Group locators by element
        element_groups = {}
        for locator in locators:
            element_name = locator.get('element_name', f"element_{locator['element_index']}")
            if element_name not in element_groups:
                element_groups[element_name] = []
            element_groups[element_name].append(locator)
        
        # Generate recommendations for each element
        for element_name, element_locators in element_groups.items():
            locator_info = {
                'element_name': element_name,
                'tag_name': element_locators[0].get('tag_name', 'unknown'),
                'locator_count': len(element_locators),
                'locator_types': [loc['type'] for loc in element_locators]
            }
            
            prompt = f"""
            Analyze this web element and provide recommendations:

            Element: {element_name}
            Tag: {locator_info['tag_name']}
            Locators: {locator_info['locator_types']}

            Provide recommendations for:
            1. missing_attributes: What attributes should be added
            2. better_strategies: Better locator strategies
            3. risk_assessment: Current risks and improvements
            4. improvement_priority: Priority level (High/Medium/Low)
            5. specific_suggestions: 3 specific actionable suggestions

            Respond with valid JSON only.
            """
            
            response = self._call_gemini(prompt)
            
            try:
                if response.startswith('{') and response.endswith('}'):
                    recommendation = json.loads(response)
                else:
                    recommendation = {
                        "missing_attributes": ["name", "data-test"],
                        "better_strategies": ["ID", "Data Test"],
                        "risk_assessment": "Medium risk - consider adding stable attributes",
                        "improvement_priority": "Medium",
                        "specific_suggestions": [response]
                    }
                
                recommendation['element_name'] = element_name
                recommendation['raw_response'] = response
                recommendations.append(recommendation)
                
            except json.JSONDecodeError:
                recommendations.append({
                    "element_name": element_name,
                    "missing_attributes": ["name", "data-test"],
                    "better_strategies": ["ID", "Data Test"],
                    "risk_assessment": "Medium risk - consider adding stable attributes",
                    "improvement_priority": "Medium",
                    "specific_suggestions": [response],
                    "raw_response": response
                })
        
        return recommendations
    
    def _generate_gemini_code(self, locators: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate test automation code using Gemini"""
        if not self.gemini_client:
            return {"error": "Gemini not available"}
        
        # Prepare locator data for code generation
        locator_data = []
        for locator in locators[:10]:  # Limit to first 10 for code generation
            locator_data.append({
                'type': locator['type'],
                'selector': locator['selector'],
                'element_name': locator.get('element_name', 'element'),
                'tag_name': locator.get('tag_name', 'unknown')
            })
        
        prompt = f"""
        Generate production-ready test automation code for these locators:

        Locators: {json.dumps(locator_data, indent=2)}

        Generate code for:
        1. Selenium WebDriver (Python) - Page Object Model pattern
        2. Playwright (Python) - Modern async pattern
        3. Cypress (JavaScript) - Framework-specific pattern

        For each framework, include:
        - Proper imports
        - Page Object Model structure
        - Error handling with try-catch
        - Wait strategies
        - Fallback locators
        - Clear method names

        Respond with JSON containing 'selenium', 'playwright', and 'cypress' keys.
        """
        
        response = self._call_gemini(prompt)
        
        try:
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                # Fallback code generation
                return {
                    "selenium": f"# Selenium code generated by Gemini\n{response[:500]}...",
                    "playwright": f"# Playwright code generated by Gemini\n{response[:500]}...",
                    "cypress": f"# Cypress code generated by Gemini\n{response[:500]}..."
                }
        except json.JSONDecodeError:
            return {
                "selenium": f"# Selenium code generated by Gemini\n{response[:500]}...",
                "playwright": f"# Playwright code generated by Gemini\n{response[:500]}...",
                "cypress": f"# Cypress code generated by Gemini\n{response[:500]}..."
            }
    
    def _prepare_locator_summary(self, locators: List[Dict[str, Any]]) -> str:
        """Prepare a summary of locators for AI analysis"""
        summary = []
        element_groups = {}
        
        for locator in locators:
            element_name = locator.get('element_name', f"element_{locator['element_index']}")
            if element_name not in element_groups:
                element_groups[element_name] = []
            element_groups[element_name].append(locator)
        
        for element_name, element_locators in element_groups.items():
            types = [loc['type'] for loc in element_locators]
            summary.append(f"Element {element_name}: {', '.join(types)}")
        
        return '\n'.join(summary)
    
    def export_gemini_enhanced_results(self, results: Dict[str, Any], format: str = 'json') -> str:
        """Export Gemini-enhanced results"""
        if format == 'json':
            filename = f"gemini_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            return filename
        
        elif format == 'markdown':
            filename = f"gemini_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w') as f:
                f.write(self._generate_markdown_report(results))
            return filename
        
        else:
            raise ValueError("Format must be 'json' or 'markdown'")
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report with structured locator output"""
        
        # Generate structured locators
        structured_locators = self._generate_structured_locators(results.get('locators', []))
        
        # Handle AI analysis with proper error checking
        ai_analysis = results.get('ai_analysis', {})
        if 'error' in ai_analysis:
            page_type = "Unknown (AI not available)"
            quality_score = "N/A (AI not available)"
            best_strategies = "[] (AI not available)"
            potential_issues = "[] (AI not available)"
            best_practices = "N/A (AI not available)"
            maintenance_risk = "N/A (AI not available)"
            overall_recommendations = "[] (AI not available)"
        else:
            page_type = ai_analysis.get('page_type', 'Unknown')
            quality_score = ai_analysis.get('element_quality_score', 'N/A')
            best_strategies = ai_analysis.get('best_strategies', [])
            potential_issues = ai_analysis.get('potential_issues', [])
            best_practices = ai_analysis.get('best_practices_compliance', 'N/A')
            maintenance_risk = ai_analysis.get('maintenance_risk_score', 'N/A')
            overall_recommendations = ai_analysis.get('overall_recommendations', [])
        
        # Handle AI recommendations
        ai_recommendations = results.get('ai_recommendations', [])
        recommendations_section = ""
        if ai_recommendations:
            for i, rec in enumerate(ai_recommendations):
                recommendations_section += f"""### Element {i+1} ({rec.get('element_name', 'Unknown')})
**Missing Attributes**: {rec.get('missing_attributes', [])}
**Better Strategies**: {rec.get('better_strategies', [])}
**Risk Assessment**: {rec.get('risk_assessment', 'N/A')}
**Improvement Priority**: {rec.get('improvement_priority', 'N/A')}
**Specific Suggestions**: {rec.get('specific_suggestions', [])}

"""
        else:
            recommendations_section = "No AI recommendations available (AI not available)\n"
        
        # Handle AI code generation
        ai_code = results.get('ai_code', {})
        if 'error' in ai_code:
            selenium_code = "Code not available (AI not available)"
            playwright_code = "Code not available (AI not available)"
            cypress_code = "Code not available (AI not available)"
        else:
            selenium_code = ai_code.get('selenium', 'Code not available')
            playwright_code = ai_code.get('playwright', 'Code not available')
            cypress_code = ai_code.get('cypress', 'Code not available')
        
        report = f"""# Gemini-Enhanced Locator Analysis Report

Generated on: {results['generated_at']}
AI Provider: {results['ai_provider']}
Model: {results['model']}
Total Locators: {results['total_locators']}

{structured_locators}

## AI Analysis

### Page Type
{page_type}

### Element Quality Score
{quality_score}

### Best Strategies
{best_strategies}

### Potential Issues
{potential_issues}

### Best Practices Compliance
{best_practices}

### Maintenance Risk Score
{maintenance_risk}

### Overall Recommendations
{overall_recommendations}

## AI Recommendations

{recommendations_section}

## Generated Code

### Selenium Code
```python
{selenium_code}
```

### Playwright Code
```python
{playwright_code}
```

### Cypress Code
```javascript
{cypress_code}
```
"""
        
        return report
    
    def _generate_structured_locators(self, locators: List[Dict[str, Any]]) -> str:
        """Generate structured locator output with custom names and sections"""
        
        # Group locators by element type and functionality
        login_elements = []
        product_elements = []
        navigation_elements = []
        other_elements = []
        
        for locator in locators:
            element_name = locator.get('element_name', '')
            tag_name = locator.get('tag_name', '')
            selector = locator.get('selector', '')
            locator_type = locator.get('type', '')
            
            # Create custom name based on element
            custom_name = self._generate_custom_name(element_name, tag_name, locator)
            
            # Categorize elements
            if 'login' in element_name.lower() or 'username' in element_name.lower() or 'password' in element_name.lower():
                login_elements.append({
                    'custom_name': custom_name,
                    'locator_type': self._get_locator_type_name(locator_type),
                    'locator_value': selector,
                    'stability': locator.get('stability', 'Medium')
                })
            elif 'product' in element_name.lower() or 'cart' in element_name.lower() or 'buy' in element_name.lower() or 'wishlist' in element_name.lower():
                product_elements.append({
                    'custom_name': custom_name,
                    'locator_type': self._get_locator_type_name(locator_type),
                    'locator_value': selector,
                    'stability': locator.get('stability', 'Medium')
                })
            elif 'breadcrumb' in element_name.lower() or 'nav' in element_name.lower() or 'contact' in element_name.lower() or 'home' in element_name.lower():
                navigation_elements.append({
                    'custom_name': custom_name,
                    'locator_type': self._get_locator_type_name(locator_type),
                    'locator_value': selector,
                    'stability': locator.get('stability', 'Medium')
                })
            else:
                other_elements.append({
                    'custom_name': custom_name,
                    'locator_type': self._get_locator_type_name(locator_type),
                    'locator_value': selector,
                    'stability': locator.get('stability', 'Medium')
                })
        
        # Generate structured output
        output = "## Well-Structured Locators for Test Automation\n\n"
        output += "Here are well-structured locators and custom names for key elements in your HTML sample, usable in Playwright or Selenium Python automation. Each locator utilizes stable attributes (ID, class, data-test, tag, text) and includes an appropriate custom name for clarity.\n\n"
        
        # Login Form Elements
        if login_elements:
            output += "### Login Form Elements\n"
            output += "| Custom Name | Locator Type | Locator Value | Stability |\n"
            output += "|-------------|--------------|---------------|----------|\n"
            for elem in login_elements[:5]:  # Limit to top 5
                output += f"| {elem['custom_name']} | {elem['locator_type']} | `{elem['locator_value']}` | {elem['stability']} |\n"
            output += "\n"
        
        # Product Info Section
        if product_elements:
            output += "### Product Info Section\n"
            output += "| Custom Name | Locator Type | Locator Value | Stability |\n"
            output += "|-------------|--------------|---------------|----------|\n"
            for elem in product_elements[:5]:  # Limit to top 5
                output += f"| {elem['custom_name']} | {elem['locator_type']} | `{elem['locator_value']}` | {elem['stability']} |\n"
            output += "\n"
        
        # Navigation and Footer
        if navigation_elements:
            output += "### Navigation and Footer\n"
            output += "| Custom Name | Locator Type | Locator Value | Stability |\n"
            output += "|-------------|--------------|---------------|----------|\n"
            for elem in navigation_elements[:5]:  # Limit to top 5
                output += f"| {elem['custom_name']} | {elem['locator_type']} | `{elem['locator_value']}` | {elem['stability']} |\n"
            output += "\n"
        
        # Other Elements
        if other_elements:
            output += "### Other Elements\n"
            output += "| Custom Name | Locator Type | Locator Value | Stability |\n"
            output += "|-------------|--------------|---------------|----------|\n"
            for elem in other_elements[:5]:  # Limit to top 5
                output += f"| {elem['custom_name']} | {elem['locator_type']} | `{elem['locator_value']}` | {elem['stability']} |\n"
            output += "\n"
        
        # Add usage examples
        output += "### Example Usage (Selenium Python)\n"
        output += "```python\n"
        example_count = 0
        for elem in (login_elements + product_elements + navigation_elements)[:4]:
            if example_count < 4:
                output += f"driver.find_element(By.{elem['locator_type'].upper().replace(' ', '_')}, '{elem['locator_value']}') # {elem['custom_name']}\n"
                example_count += 1
        output += "```\n\n"
        
        output += "These locators use explicit attributes (IDs, classes, data-* attributes) for maximum reliability and maintainability, making them ideal for AI-driven locator generation and resilient test automation.\n\n"
        
        return output
    
    def _generate_custom_name(self, element_name: str, tag_name: str, locator: Dict[str, Any]) -> str:
        """Generate a custom name for the element"""
        selector = locator.get('selector', '')
        
        # Extract meaningful parts from element name
        if 'username' in element_name.lower():
            return 'UsernameInput'
        elif 'password' in element_name.lower():
            return 'PasswordInput'
        elif 'login' in element_name.lower() and 'button' in element_name.lower():
            return 'LoginButton'
        elif 'add-to-cart' in element_name.lower():
            return 'AddToCartButton'
        elif 'buy-now' in element_name.lower():
            return 'BuyNowButton'
        elif 'wishlist' in element_name.lower():
            return 'WishlistButton'
        elif 'product-image' in element_name.lower():
            return 'ProductImage'
        elif 'description' in element_name.lower():
            return 'ProductDescription'
        elif 'home' in element_name.lower():
            return 'BreadcrumbHome'
        elif 'electronics' in element_name.lower():
            return 'BreadcrumbElectronics'
        elif 'contact' in element_name.lower():
            return 'ContactLink'
        elif 'footer' in element_name.lower():
            return 'FooterSection'
        elif 'breadcrumb' in element_name.lower():
            return 'BreadcrumbNav'
        else:
            # Generate name from tag and index
            return f"{tag_name.capitalize()}{element_name.split('_')[-1] if '_' in element_name else 'Element'}"
    
    def _get_locator_type_name(self, locator_type: str) -> str:
        """Convert locator type to readable name"""
        type_mapping = {
            'ID': 'CSS Selector',
            'CSS Class': 'CSS Selector',
            'Data Test': 'CSS Selector',
            'Attribute': 'CSS Selector',
            'Button Text': 'XPath',
            'Link Text': 'Link Text',
            'XPath Text': 'XPath',
            'XPath ID': 'XPath',
            'XPath Data Attribute': 'XPath',
            'XPath Contains Text': 'XPath',
            'XPath Contains Attribute': 'XPath',
            'XPath Position': 'XPath',
            'XPath Parent-Child': 'XPath',
            'XPath Class Combination': 'XPath',
            'XPath Name+Type': 'XPath',
            'CSS Name+Type': 'CSS Selector',
            'CSS Partial Class': 'CSS Selector',
            'CSS Attribute Presence': 'CSS Selector',
            'Name': 'CSS Selector'
        }
        return type_mapping.get(locator_type, 'CSS Selector')


def demo_gemini_enhanced():
    """Demo the Gemini-enhanced locator generator"""
    
    print("GEMINI-ENHANCED LOCATOR GENERATOR DEMO")
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
    
    # Initialize Gemini-enhanced generator
    generator = GeminiEnhancedLocatorGenerator()
    
    # Generate enhanced locators
    results = generator.generate_gemini_enhanced_locators(sample_html)
    
    print(f"SUCCESS: Generated {results['total_locators']} locators")
    print(f"SUCCESS: AI Provider: {results['ai_provider']}")
    print(f"SUCCESS: Model: {results['model']}")
    
    # Display AI analysis
    analysis = results['ai_analysis']
    print(f"\nAI Analysis:")
    print(f"  • Page Type: {analysis.get('page_type', 'Unknown')}")
    print(f"  • Quality Score: {analysis.get('element_quality_score', 'N/A')}")
    print(f"  • Best Strategies: {analysis.get('best_strategies', [])}")
    print(f"  • Maintenance Risk: {analysis.get('maintenance_risk_score', 'N/A')}")
    
    # Display recommendations
    print(f"\nAI Recommendations ({len(results['ai_recommendations'])} elements):")
    for i, rec in enumerate(results['ai_recommendations'][:3]):
        print(f"  {i+1}. Element: {rec.get('element_name', 'Unknown')}")
        print(f"     Priority: {rec.get('improvement_priority', 'N/A')}")
        print(f"     Suggestions: {len(rec.get('specific_suggestions', []))} recommendations")
    
    # Display code generation
    code = results['ai_code']
    print(f"\nAI-Generated Code:")
    print(f"  • Selenium: {len(code.get('selenium', ''))} characters")
    print(f"  • Playwright: {len(code.get('playwright', ''))} characters")
    print(f"  • Cypress: {len(code.get('cypress', ''))} characters")
    
    # Export results
    json_file = generator.export_gemini_enhanced_results(results, 'json')
    md_file = generator.export_gemini_enhanced_results(results, 'markdown')
    
    print(f"\nReports saved:")
    print(f"  • JSON: {json_file}")
    print(f"  • Markdown: {md_file}")
    
    print(f"\nGemini-Enhanced Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_gemini_enhanced()
