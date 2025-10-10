# Phoenix Smart Locator AI

An intelligent web element locator generator that provides comprehensive locator strategies with optional AI enhancement using Google Gemini.

## 🚀 Features

### Core Features (No AI Required)
- ✅ **ALL web elements detection** - Finds every element on the page
- ✅ **Intelligent element naming** - Context-aware naming based on attributes
- ✅ **Priority-based suggestions** - High/Medium/Low priority recommendations
- ✅ **Comprehensive locator generation** - Multiple locator strategies per element
- ✅ **Export functionality** - JSON, CSV, and code generation

### AI-Enhanced Features (Gemini Optional)
- 🧠 **Intelligent page analysis** - Detects page type and quality scores
- 🎯 **Advanced recommendations** - Element-specific improvement suggestions
- 💻 **Production-ready code** - Generates Selenium, Playwright, Cypress code
- 📊 **Risk assessment** - Identifies potential issues and maintenance risks

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd Phoenix-SmartLocatorAI

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### Basic Usage (No AI)
```python
from locator_generator import LocatorGenerator

generator = LocatorGenerator()
locators = generator.generate_locators(html_content)

for locator in locators:
    print(f"Element: {locator['element_name']}")
    print(f"Type: {locator['type']}")
    print(f"Selector: {locator['selector']}")
    print(f"High Priority: {locator['suggestions']['High']}")
```

### AI-Enhanced Usage (Gemini)
```python
from gemini_enhanced_locator_generator import GeminiEnhancedLocatorGenerator

# Set your Gemini API key
import os
os.environ['GOOGLE_API_KEY'] = 'your_api_key_here'

generator = GeminiEnhancedLocatorGenerator()
results = generator.generate_gemini_enhanced_locators(html_content)

print(f"Page Type: {results['ai_analysis']['page_type']}")
print(f"Quality Score: {results['ai_analysis']['element_quality_score']}")
```

## 🎮 Demo Scripts

```bash
# Pure Python demo (no AI required)
python pure_python_demo.py

# Gemini-enhanced demo (requires API key)
python gemini_demo.py

# Enhanced features demo
python enhanced_demo.py
```

## 🔧 Setup for AI Features

1. **Get Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Set Environment Variable**:
   ```bash
   # Windows
   $env:GOOGLE_API_KEY='your_api_key_here'
   
   # Linux/Mac
   export GOOGLE_API_KEY='your_api_key_here'
   ```
3. **Install AI Dependencies**:
   ```bash
   pip install google-generativeai
   ```

## 📊 Example Output

### Core Features
```
✅ Found 145 locators for ALL web elements
✅ Found 21 unique elements with intelligent names

💡 Priority Suggestions:
  🔴 High: Use ID selector: #login-btn - Most reliable and fast
  🟡 Medium: Combine with other attributes: #login-btn[class*='specific-class']
  🟢 Low: Use XPath equivalent: //*[@id='login-btn']
```

### AI-Enhanced Features
```
🧠 AI Analysis:
  • Page Type: e-commerce
  • Quality Score: 8/10
  • Best Strategies: ['Data Test', 'ID', 'XPath Data Attribute']
  • Maintenance Risk: 4/10

💻 AI-Generated Code:
  • Selenium: 3,034 characters
  • Playwright: 4,358 characters
  • Cypress: 3,371 characters
```

## 📁 Project Structure

```
Phoenix-SmartLocatorAI/
├── locator_generator.py                    # Core system
├── gemini_enhanced_locator_generator.py    # AI enhancement
├── pure_python_demo.py                     # Basic demo
├── gemini_demo.py                          # AI demo
├── enhanced_demo.py                        # Features demo
├── requirements.txt                        # Dependencies
└── README.md                              # This file
```

## 🎯 Use Cases

- **Test Automation**: Generate reliable locators for Selenium, Playwright, Cypress
- **Web Scraping**: Find and identify elements for data extraction
- **Quality Assurance**: Analyze page structure and element stability
- **Development**: Understand element relationships and naming conventions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For questions or issues, please open an issue on the repository.
