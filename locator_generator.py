"""
Locator Generator - Enhanced Core Engine
Generates advanced locators from HTML/DOM or URLs for web automation
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Union
import requests
from urllib.parse import urlparse
import re
import json
from datetime import datetime


class LocatorGenerator:
    """
    Enhanced locator generator that takes HTML/DOM or URL and finds locators for elements
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.soup = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Default configuration
        self.config = {
            'include_basic_locators': True,
            'include_xpath_locators': True,
            'include_advanced_css': True,
            'include_dynamic_locators': True,
            'max_text_length': 50,
            'stability_weights': {
                'High': 3,
                'Medium': 2,
                'Low': 1
            },
            'preferred_locator_types': ['ID', 'Data Test', 'XPath ID', 'XPath Data Attribute'],
            'exclude_locator_types': [],
            'min_stability_score': 0,
            'enable_shadow_dom_detection': True,
            'enable_iframe_detection': True,
            'enable_stability_analysis': True
        }
        
        # Update with user config
        if config:
            self.config.update(config)
    
    def _fetch_html_from_url(self, url: str) -> str:
        """
        Fetch HTML content from a URL
        
        Args:
            url: URL to fetch HTML from
            
        Returns:
            HTML content as string
            
        Raises:
            requests.RequestException: If URL cannot be fetched
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch URL {url}: {str(e)}")
    
    def _is_url(self, input_string: str) -> bool:
        """
        Check if the input string is a valid URL
        
        Args:
            input_string: String to check
            
        Returns:
            True if it's a valid URL, False otherwise
        """
        try:
            result = urlparse(input_string)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def generate_locators(self, html_or_url: str, target_selector: str = None) -> List[Dict[str, Any]]:
        """
        Generate locators for elements in HTML or from a URL
        
        Args:
            html_or_url: HTML content as string OR URL to fetch HTML from
            target_selector: CSS selector for target element (optional)
            
        Returns:
            List of locator dictionaries
            
        Raises:
            requests.RequestException: If URL cannot be fetched
        """
        # Determine if input is URL or HTML content
        if self._is_url(html_or_url):
            print(f"🌐 Fetching HTML from URL: {html_or_url}")
            html_content = self._fetch_html_from_url(html_or_url)
        else:
            html_content = html_or_url
        
        # Parse HTML
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find target element(s)
        if target_selector:
            target_elements = [self.soup.select_one(target_selector)]
        else:
            # Find ALL web elements (not just interactive ones)
            target_elements = self._find_all_web_elements()
        
        if not target_elements or not any(target_elements):
            return []
        
        # Generate locators for all target elements
        all_locators = []
        
        for element_index, target_element in enumerate(target_elements):
            if not target_element:
                continue
                
            # Generate locators for the current element
            element_locators = []
            element_name = self._generate_element_name(target_element, element_index)
            
            # Basic locators
            if self.config['include_basic_locators']:
                basic_locators = self._generate_basic_locators(target_element, element_index)
                for locator in basic_locators:
                    locator['element_name'] = element_name
                    locator = self._add_priority_suggestions(locator, target_element)
                element_locators.extend(basic_locators)
            
            # Advanced XPath locators
            if self.config['include_xpath_locators']:
                xpath_locators = self._generate_xpath_locators(target_element)
                for xpath in xpath_locators:
                    xpath['element_index'] = element_index
                    xpath['tag_name'] = target_element.name
                    xpath['element_name'] = element_name
                    xpath = self._add_priority_suggestions(xpath, target_element)
                element_locators.extend(xpath_locators)
            
            # Advanced CSS locators
            if self.config['include_advanced_css']:
                css_locators = self._generate_advanced_css_locators(target_element)
                for css in css_locators:
                    css['element_index'] = element_index
                    css['tag_name'] = target_element.name
                    css['element_name'] = element_name
                    css = self._add_priority_suggestions(css, target_element)
                element_locators.extend(css_locators)
            
            # Dynamic locators
            if self.config['include_dynamic_locators']:
                dynamic_locators = self.generate_dynamic_locators(target_element)
                for dynamic in dynamic_locators:
                    dynamic['element_index'] = element_index
                    dynamic['tag_name'] = target_element.name
                    dynamic['element_name'] = element_name
                    dynamic = self._add_priority_suggestions(dynamic, target_element)
                element_locators.extend(dynamic_locators)
            
            # Filter locators based on configuration
            filtered_locators = self._filter_locators_by_config(element_locators)
            all_locators.extend(filtered_locators)
        
        return all_locators
    
    def _find_first_interactive_element(self):
        """Find the first interactive element on the page"""
        interactive_selectors = [
            'button', 'input', 'select', 'textarea', 'a',
            '[onclick]', '[role="button"]', '[tabindex]'
        ]
        
        for selector in interactive_selectors:
            element = self.soup.select_one(selector)
            if element:
                return element
        
        return None
    
    def _find_all_interactive_elements(self):
        """Find all interactive elements on the page"""
        interactive_selectors = [
            'button', 'input', 'select', 'textarea', 'a',
            '[onclick]', '[role="button"]', '[tabindex]'
        ]
        
        all_elements = []
        for selector in interactive_selectors:
            elements = self.soup.select(selector)
            all_elements.extend(elements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for element in all_elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        return unique_elements
    
    def _find_all_web_elements(self):
        """Find ALL web elements on the page (not just interactive ones)"""
        if not self.soup:
            return []
        
        # Include all common HTML elements
        all_tags = [
            'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'button', 'input', 'select', 'textarea', 'a', 'form', 'label',
            'img', 'nav', 'header', 'footer', 'main', 'section', 'article',
            'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
            'iframe', 'video', 'audio', 'canvas', 'svg', 'path', 'g',
            'meta', 'link', 'script', 'style', 'title', 'head', 'body'
        ]
        
        all_elements = []
        for tag in all_tags:
            elements = self.soup.find_all(tag)
            all_elements.extend(elements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for element in all_elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        return unique_elements
    
    def _generate_element_name(self, element, index: int) -> str:
        """Generate an appropriate name for the element based on its context"""
        tag_name = element.name
        attrs = element.attrs or {}
        
        # Priority 1: Use ID if available
        if 'id' in attrs:
            return f"{tag_name}_{attrs['id']}"
        
        # Priority 2: Use data-test attribute
        if 'data-test' in attrs:
            return f"{tag_name}_{attrs['data-test']}"
        
        # Priority 3: Use name attribute
        if 'name' in attrs:
            return f"{tag_name}_{attrs['name']}"
        
        # Priority 4: Use class names (first meaningful class)
        if 'class' in attrs and attrs['class']:
            classes = attrs['class']
            # Filter out generic classes
            meaningful_classes = [cls for cls in classes if cls not in ['btn', 'form-control', 'container', 'row', 'col']]
            if meaningful_classes:
                return f"{tag_name}_{meaningful_classes[0]}"
        
        # Priority 5: Use text content for buttons/links
        if tag_name in ['button', 'a']:
            text = element.get_text(strip=True)
            if text:
                # Clean text for naming
                clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
                clean_text = re.sub(r'\s+', '_', clean_text.strip())
                if clean_text and len(clean_text) <= 30:
                    return f"{tag_name}_{clean_text.lower()}"
        
        # Priority 6: Use href for links
        if tag_name == 'a' and 'href' in attrs:
            href = attrs['href']
            if href.startswith('/'):
                href = href[1:]
            href_clean = re.sub(r'[^a-zA-Z0-9\s]', '_', href)
            return f"link_{href_clean[:20]}"
        
        # Priority 7: Use src for images
        if tag_name == 'img' and 'src' in attrs:
            src = attrs['src']
            if src:
                # Extract filename without extension
                filename = src.split('/')[-1].split('.')[0]
                if filename:
                    return f"img_{filename}"
        
        # Priority 8: Use type for inputs
        if tag_name == 'input' and 'type' in attrs:
            input_type = attrs['type']
            return f"input_{input_type}_{index}"
        
        # Priority 9: Use placeholder for inputs
        if tag_name == 'input' and 'placeholder' in attrs:
            placeholder = attrs['placeholder']
            clean_placeholder = re.sub(r'[^a-zA-Z0-9\s]', '', placeholder)
            clean_placeholder = re.sub(r'\s+', '_', clean_placeholder.strip())
            if clean_placeholder:
                return f"input_{clean_placeholder.lower()}"
        
        # Priority 10: Use role attribute
        if 'role' in attrs:
            return f"{tag_name}_{attrs['role']}_{index}"
        
        # Priority 11: Use aria-label
        if 'aria-label' in attrs:
            aria_label = attrs['aria-label']
            clean_label = re.sub(r'[^a-zA-Z0-9\s]', '', aria_label)
            clean_label = re.sub(r'\s+', '_', clean_label.strip())
            if clean_label:
                return f"{tag_name}_{clean_label.lower()}"
        
        # Fallback: Use tag name with index
        return f"{tag_name}_{index}"
    
    def _add_priority_suggestions(self, locator: Dict[str, Any], element) -> Dict[str, Any]:
        """Add priority-based suggestions to a locator"""
        locator_type = locator['type']
        selector = locator['selector']
        
        if locator_type == 'ID':
            locator['suggestions'] = {
                'High': f"Use ID selector: {selector} - Most reliable and fast",
                'Medium': f"Combine with other attributes: {selector}[class*='specific-class']",
                'Low': f"Use XPath equivalent: //*[@id='{locator['value']}']"
            }
        elif locator_type == 'CSS Class':
            classes = locator['value'].split()
            locator['suggestions'] = {
                'High': f"Use specific class: .{classes[0]} - More specific than multiple classes",
                'Medium': f"Use all classes: {selector} - Current approach",
                'Low': f"Use partial class match: [class*='{classes[0]}'] - More flexible"
            }
        elif locator_type == 'Name':
            locator['suggestions'] = {
                'High': f"Use name attribute: [name='{locator['value']}'] - Good for forms",
                'Medium': f"Combine with tag: {element.name}[name='{locator['value']}'] - More specific",
                'Low': f"Use XPath: //*[@name='{locator['value']}'] - Alternative approach"
            }
        elif locator_type == 'Data Test':
            locator['suggestions'] = {
                'High': f"Use data-test: {selector} - Designed for testing",
                'Medium': f"Combine with tag: {element.name}{selector} - More specific",
                'Low': f"Use XPath: //*[@data-test='{locator['value']}'] - Alternative approach"
            }
        elif locator_type == 'Link Text':
            locator['suggestions'] = {
                'High': f"Use link text: {selector} - Direct text match",
                'Medium': f"Use partial text: [href*='partial-url'] - More flexible",
                'Low': f"Use XPath text: //a[contains(text(), '{locator['value'][:20]}...')] - Partial match"
            }
        elif locator_type == 'Button Text':
            locator['suggestions'] = {
                'High': f"Use button text: {selector} - Direct text match",
                'Medium': f"Use partial text: button[contains(text(), '{locator['value'][:15]}...')] - Partial match",
                'Low': f"Use XPath: //button[contains(text(), '{locator['value'][:15]}...')] - Alternative"
            }
        else:
            # Generic suggestions for other types
            locator['suggestions'] = {
                'High': f"Use primary selector: {selector} - Recommended approach",
                'Medium': f"Use alternative: {selector.replace('=', '*=')} - More flexible",
                'Low': f"Use XPath equivalent: //*[@attribute='{locator.get('value', 'value')}'] - Alternative"
            }
        
        return locator
    
    def _generate_basic_locators(self, element, element_index: int) -> List[Dict[str, Any]]:
        """Generate basic locators for an element"""
        basic_locators = []
        
        # ID locator
        if element.get('id'):
            basic_locators.append({
                'type': 'ID',
                'value': element.get('id'),
                'selector': f"#{element.get('id')}",
                'stability': 'High',
                'explanation': 'Direct ID selector - most stable',
                'element_index': element_index,
                'tag_name': element.name,
                'element_name': self._generate_element_name(element, element_index),
                'priority': 'High',
                'suggestions': {
                    'High': f"Use ID selector: #{element.get('id')} - Most reliable and fast",
                    'Medium': f"Combine with other attributes: #{element.get('id')}[class*='specific-class']",
                    'Low': f"Use XPath equivalent: //*[@id='{element.get('id')}']"
                }
            })
        
        # Class locator
        if element.get('class'):
            classes = ' '.join(element.get('class'))
            basic_locators.append({
                'type': 'CSS Class',
                'value': classes,
                'selector': f".{'.'.join(element.get('class'))}",
                'stability': 'Medium',
                'explanation': 'CSS class selector - good for styling-based selection',
                'element_index': element_index,
                'tag_name': element.name,
                'element_name': self._generate_element_name(element, element_index),
                'priority': 'Medium',
                'suggestions': {
                    'High': f"Use specific class: .{element.get('class')[0]} - More specific than multiple classes",
                    'Medium': f"Use all classes: .{'.'.join(element.get('class'))} - Current approach",
                    'Low': f"Use partial class match: [class*='{element.get('class')[0]}'] - More flexible"
                }
            })
        
        # Name locator
        if element.get('name'):
            basic_locators.append({
                'type': 'Name',
                'value': element.get('name'),
                'selector': f"[name='{element.get('name')}']",
                'stability': 'Medium',
                'explanation': 'Name attribute selector - good for form elements',
                'element_index': element_index,
                'tag_name': element.name
            })
        
        # Data-test locator
        if element.get('data-test'):
            basic_locators.append({
                'type': 'Data Test',
                'value': element.get('data-test'),
                'selector': f"[data-test='{element.get('data-test')}']",
                'stability': 'High',
                'explanation': 'Data-test attribute - designed for testing',
                'element_index': element_index,
                'tag_name': element.name
            })
        
        # Text content locator (for buttons/links)
        text_content = element.get_text(strip=True)
        if text_content and len(text_content) < 50:
            if element.name == 'a':
                basic_locators.append({
                    'type': 'Link Text',
                    'value': text_content,
                    'selector': f"//a[text()='{text_content}']",
                    'stability': 'Low',
                    'explanation': 'Link text selector - may change with UI updates',
                    'element_index': element_index,
                    'tag_name': element.name
                })
            elif element.name == 'button':
                basic_locators.append({
                    'type': 'Button Text',
                    'value': text_content,
                    'selector': f"//button[text()='{text_content}']",
                    'stability': 'Low',
                    'explanation': 'Button text selector - may change with UI updates',
                    'element_index': element_index,
                    'tag_name': element.name
                })
        
        # Tag + attribute combination
        tag_name = element.name
        for attr, value in element.attrs.items():
            if attr not in ['id', 'class', 'name', 'data-test'] and value:
                basic_locators.append({
                    'type': 'Attribute',
                    'value': f"{attr}='{value}'",
                    'selector': f"{tag_name}[{attr}='{value}']",
                    'stability': 'Medium',
                    'explanation': f'Element with {attr} attribute',
                    'element_index': element_index,
                    'tag_name': element.name
                })
        
        return basic_locators
    
    def _filter_locators_by_config(self, locators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter locators based on configuration settings"""
        filtered = []
        
        for locator in locators:
            # Check if locator type is excluded
            if locator['type'] in self.config['exclude_locator_types']:
                continue
            
            # Check minimum stability score
            if hasattr(self, '_calculate_locator_score'):
                score = self._calculate_locator_score(locator)
                if score < self.config['min_stability_score']:
                    continue
            
            filtered.append(locator)
        
        return filtered
    
    def _calculate_locator_score(self, locator: Dict[str, Any]) -> float:
        """Calculate a score for a locator based on configuration"""
        base_score = self.config['stability_weights'].get(locator['stability'], 1)
        
        # Bonus for preferred types
        if locator['type'] in self.config['preferred_locator_types']:
            base_score += 1
        
        return base_score
    
    def _generate_xpath_locators(self, element) -> List[Dict[str, Any]]:
        """Generate advanced XPath locators for an element"""
        xpath_locators = []
        
        # XPath by ID
        if element.get('id'):
            xpath_locators.append({
                'type': 'XPath ID',
                'value': element.get('id'),
                'selector': f"//*[@id='{element.get('id')}']",
                'stability': 'High',
                'explanation': 'XPath by ID - most reliable XPath strategy'
            })
        
        # XPath by text content (for buttons, links, labels)
        text_content = element.get_text(strip=True)
        if text_content and len(text_content) < 50:
            if element.name in ['button', 'a', 'label', 'span', 'div']:
                xpath_locators.append({
                    'type': 'XPath Text',
                    'value': text_content,
                    'selector': f"//{element.name}[text()='{text_content}']",
                    'stability': 'Medium',
                    'explanation': f'XPath by text content for {element.name}'
                })
        
        # XPath by attribute combinations
        if element.get('name') and element.get('type'):
            xpath_locators.append({
                'type': 'XPath Name+Type',
                'value': f"{element.get('name')}+{element.get('type')}",
                'selector': f"//{element.name}[@name='{element.get('name')}' and @type='{element.get('type')}']",
                'stability': 'High',
                'explanation': 'XPath by name and type combination - very stable'
            })
        
        # XPath by data attributes
        for attr in element.attrs:
            if attr.startswith('data-'):
                xpath_locators.append({
                    'type': 'XPath Data Attribute',
                    'value': f"{attr}='{element.get(attr)}'",
                    'selector': f"//{element.name}[@{attr}='{element.get(attr)}']",
                    'stability': 'High',
                    'explanation': f'XPath by {attr} - designed for testing'
                })
        
        # XPath by position (nth-child)
        if element.parent:
            siblings = element.parent.find_all(element.name, recursive=False)
            if len(siblings) > 1:
                position = siblings.index(element) + 1
                xpath_locators.append({
                    'type': 'XPath Position',
                    'value': f"{element.name}[{position}]",
                    'selector': f"//{element.name}[{position}]",
                    'stability': 'Low',
                    'explanation': f'XPath by position - fragile if DOM structure changes'
                })
        
        # XPath by parent-child relationship
        if element.parent and element.parent.get('id'):
            xpath_locators.append({
                'type': 'XPath Parent-Child',
                'value': f"parent({element.parent.get('id')})->{element.name}",
                'selector': f"//*[@id='{element.parent.get('id')}']//{element.name}",
                'stability': 'Medium',
                'explanation': 'XPath using parent ID context'
            })
        
        # XPath by class combination
        if element.get('class'):
            classes = element.get('class')
            if len(classes) > 1:
                class_selector = ' and '.join([f"contains(@class, '{cls}')" for cls in classes])
                xpath_locators.append({
                    'type': 'XPath Class Combination',
                    'value': ' '.join(classes),
                    'selector': f"//{element.name}[{class_selector}]",
                    'stability': 'Medium',
                    'explanation': 'XPath by multiple class names'
                })
        
        return xpath_locators
    
    def _generate_advanced_css_locators(self, element) -> List[Dict[str, Any]]:
        """Generate advanced CSS locators"""
        css_locators = []
        
        # CSS by attribute combinations
        if element.get('name') and element.get('type'):
            css_locators.append({
                'type': 'CSS Name+Type',
                'value': f"{element.get('name')}+{element.get('type')}",
                'selector': f"{element.name}[name='{element.get('name')}'][type='{element.get('type')}']",
                'stability': 'High',
                'explanation': 'CSS by name and type combination'
            })
        
        # CSS by partial class matching
        if element.get('class'):
            classes = element.get('class')
            for cls in classes:
                if len(cls) > 3:  # Only for meaningful class names
                    css_locators.append({
                        'type': 'CSS Partial Class',
                        'value': f"*{cls}*",
                        'selector': f"[class*='{cls}']",
                        'stability': 'Medium',
                        'explanation': f'CSS by partial class name matching'
                    })
        
        # CSS by attribute presence
        for attr in element.attrs:
            if attr not in ['id', 'class', 'name', 'type'] and attr.startswith(('data-', 'aria-', 'role')):
                css_locators.append({
                    'type': 'CSS Attribute Presence',
                    'value': f"has-{attr}",
                    'selector': f"{element.name}[{attr}]",
                    'stability': 'Medium',
                    'explanation': f'CSS by {attr} attribute presence'
                })
        
        return css_locators
    
    def get_element_info(self, html_or_url: str, target_selector: str = None) -> Dict[str, Any]:
        """
        Get information about the target element(s)
        
        Args:
            html_or_url: HTML content as string OR URL to fetch HTML from
            target_selector: CSS selector for target element (optional)
            
        Returns:
            Dictionary with element information (single element) or list of element info (multiple elements)
            
        Raises:
            requests.RequestException: If URL cannot be fetched
        """
        # Determine if input is URL or HTML content
        if self._is_url(html_or_url):
            print(f"🌐 Fetching HTML from URL: {html_or_url}")
            html_content = self._fetch_html_from_url(html_or_url)
        else:
            html_content = html_or_url
        
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        if target_selector:
            target_elements = [self.soup.select_one(target_selector)]
        else:
            target_elements = self._find_all_interactive_elements()
        
        if not target_elements or not any(target_elements):
            return {} if target_selector else []
        
        # If target_selector is provided, return single element info
        if target_selector:
            target_element = target_elements[0]
        if not target_element:
            return {}
        
        return {
            'tag_name': target_element.name,
            'attributes': dict(target_element.attrs) if target_element.attrs else {},
            'text_content': target_element.get_text(strip=True),
            'inner_html': str(target_element.contents),
            'outer_html': str(target_element)
        }
        
        # If no target_selector, return list of all interactive elements info
        elements_info = []
        for element_index, target_element in enumerate(target_elements):
            if not target_element:
                continue
                
            element_info = {
                'element_index': element_index,
                'tag_name': target_element.name,
                'attributes': dict(target_element.attrs) if target_element.attrs else {},
                'text_content': target_element.get_text(strip=True),
                'inner_html': str(target_element.contents),
                'outer_html': str(target_element)
            }
            elements_info.append(element_info)
        
        return elements_info
    
    def validate_locator(self, locator: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Validate a locator against HTML content
        
        Args:
            locator: Locator dictionary to validate
            html_content: HTML content to test against
            
        Returns:
            Validation result dictionary
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            selector = locator['selector']
            
            # Test CSS selectors
            if not selector.startswith('//'):
                elements = soup.select(selector)
                is_valid = len(elements) > 0
                uniqueness = len(elements) == 1
            else:
                # For XPath, we'll do a basic validation
                # In a real implementation, you'd use lxml or selenium for XPath validation
                is_valid = True  # Placeholder - would need proper XPath engine
                uniqueness = True  # Placeholder
            
            return {
                'is_valid': is_valid,
                'is_unique': uniqueness,
                'element_count': len(elements) if not selector.startswith('//') else 1,
                'validation_timestamp': datetime.now().isoformat(),
                'locator_type': locator['type'],
                'selector': selector
            }
        except Exception as e:
            return {
                'is_valid': False,
                'is_unique': False,
                'element_count': 0,
                'validation_timestamp': datetime.now().isoformat(),
                'error': str(e),
                'locator_type': locator['type'],
                'selector': selector
            }
    
    def rank_locators(self, locators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank locators by stability and quality using configuration
        
        Args:
            locators: List of locator dictionaries
            
        Returns:
            Ranked list of locators with scores
        """
        stability_scores = self.config['stability_weights']
        
        for locator in locators:
            # Base score from stability using config
            score = stability_scores.get(locator['stability'], 1)
            
            # Bonus for preferred locator types
            if locator['type'] in self.config['preferred_locator_types']:
                score += 2
            
            # Bonus for attribute combinations
            if '+' in locator['value']:
                score += 1
            
            # Penalty for position-based selectors
            if 'Position' in locator['type']:
                score -= 1
            
            # Penalty for text-based selectors
            if 'Text' in locator['type']:
                score -= 0.5
            
            # Bonus for dynamic-friendly locators
            if 'Contains' in locator['type']:
                score += 0.5
            
            locator['score'] = max(0, score)  # Ensure non-negative score
        
        # Sort by score (descending)
        return sorted(locators, key=lambda x: x['score'], reverse=True)
    
    def export_locators(self, locators: List[Dict[str, Any]], format_type: str = 'json', 
                       include_metadata: bool = True) -> Union[str, Dict[str, Any]]:
        """
        Export locators in various formats
        
        Args:
            locators: List of locator dictionaries
            format_type: Export format ('json', 'csv', 'selenium', 'playwright')
            include_metadata: Whether to include metadata in export
            
        Returns:
            Exported data in requested format
        """
        if format_type == 'json':
            export_data = {
                'locators': locators,
                'export_timestamp': datetime.now().isoformat(),
                'total_count': len(locators)
            }
            if include_metadata:
                export_data['metadata'] = {
                    'generator_version': '2.0',
                    'export_format': 'json'
                }
            return json.dumps(export_data, indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            headers = ['element_index', 'tag_name', 'type', 'value', 'selector', 'stability', 'score', 'explanation']
            writer.writerow(headers)
            
            # Data rows
            for locator in locators:
                row = [
                    locator.get('element_index', ''),
                    locator.get('tag_name', ''),
                    locator.get('type', ''),
                    locator.get('value', ''),
                    locator.get('selector', ''),
                    locator.get('stability', ''),
                    locator.get('score', ''),
                    locator.get('explanation', '')
                ]
                writer.writerow(row)
            
            return output.getvalue()
        
        elif format_type == 'selenium':
            selenium_code = "# Selenium WebDriver locators\n"
            selenium_code += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, locator in enumerate(locators[:10]):  # Top 10 locators
                selector = locator['selector']
                if selector.startswith('//'):
                    selenium_code += f"# {locator['type']} - {locator['explanation']}\n"
                    selenium_code += f"element_{i+1} = driver.find_element(By.XPATH, '{selector}')\n\n"
                else:
                    selenium_code += f"# {locator['type']} - {locator['explanation']}\n"
                    selenium_code += f"element_{i+1} = driver.find_element(By.CSS_SELECTOR, '{selector}')\n\n"
            
            return selenium_code
        
        elif format_type == 'playwright':
            playwright_code = "// Playwright locators\n"
            playwright_code += f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, locator in enumerate(locators[:10]):  # Top 10 locators
                selector = locator['selector']
                playwright_code += f"// {locator['type']} - {locator['explanation']}\n"
                if selector.startswith('//'):
                    playwright_code += f"const element{i+1} = page.locator('xpath={selector}');\n\n"
                else:
                    playwright_code += f"const element{i+1} = page.locator('{selector}');\n\n"
            
            return playwright_code
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def generate_smart_suggestions(self, locators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate smart locator suggestions based on context and best practices
        
        Args:
            locators: List of locator dictionaries
            
        Returns:
            List of smart suggestions
        """
        suggestions = []
        
        # Group locators by element
        elements_dict = {}
        for locator in locators:
            element_index = locator.get('element_index', 0)
            if element_index not in elements_dict:
                elements_dict[element_index] = []
            elements_dict[element_index].append(locator)
        
        for element_index, element_locators in elements_dict.items():
            element_suggestions = []
            
            # Check if element has ID
            has_id = any(loc['type'] == 'ID' for loc in element_locators)
            if not has_id:
                element_suggestions.append({
                    'type': 'Recommendation',
                    'message': f'Element {element_index} lacks an ID attribute. Consider adding one for better stability.',
                    'priority': 'High'
                })
            
            # Check for data-test attributes
            has_data_test = any('data-test' in loc['type'].lower() for loc in element_locators)
            if not has_data_test:
                element_suggestions.append({
                    'type': 'Recommendation',
                    'message': f'Element {element_index} should have a data-test attribute for testing.',
                    'priority': 'Medium'
                })
            
            # Check for high-stability locators
            high_stability_count = sum(1 for loc in element_locators if loc['stability'] == 'High')
            if high_stability_count < 2:
                element_suggestions.append({
                    'type': 'Warning',
                    'message': f'Element {element_index} has only {high_stability_count} high-stability locator(s). Consider adding more stable attributes.',
                    'priority': 'Medium'
                })
            
            # Check for text-based locators
            text_locators = [loc for loc in element_locators if 'Text' in loc['type']]
            if text_locators:
                element_suggestions.append({
                    'type': 'Warning',
                    'message': f'Element {element_index} has {len(text_locators)} text-based locator(s). These may break if UI text changes.',
                    'priority': 'Low'
                })
            
            suggestions.extend(element_suggestions)
        
        return suggestions
    
    def find_shadow_dom_elements(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Find elements that might be in Shadow DOM
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            List of potential shadow DOM elements
        """
        shadow_elements = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for custom elements (likely to have shadow DOM)
        custom_elements = soup.find_all(lambda tag: tag.name and '-' in tag.name)
        
        for element in custom_elements:
            shadow_elements.append({
                'tag_name': element.name,
                'attributes': dict(element.attrs) if element.attrs else {},
                'is_custom_element': True,
                'shadow_dom_likelihood': 'High',
                'suggested_locator': f"//{element.name}",
                'explanation': f'Custom element {element.name} likely contains shadow DOM'
            })
        
        # Look for elements with shadow-related attributes
        shadow_related = soup.find_all(attrs={'shadowroot': True})
        shadow_related.extend(soup.find_all(attrs={'shadowrootmode': True}))
        
        for element in shadow_related:
            shadow_elements.append({
                'tag_name': element.name,
                'attributes': dict(element.attrs) if element.attrs else {},
                'is_custom_element': False,
                'shadow_dom_likelihood': 'Confirmed',
                'suggested_locator': f"//{element.name}[@shadowroot]",
                'explanation': f'Element with shadow DOM attributes'
            })
        
        return shadow_elements
    
    def find_iframe_elements(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Find iframe elements and their contexts
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            List of iframe elements with context
        """
        iframe_elements = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        iframes = soup.find_all('iframe')
        
        for iframe in iframes:
            iframe_info = {
                'tag_name': 'iframe',
                'attributes': dict(iframe.attrs) if iframe.attrs else {},
                'src': iframe.get('src', ''),
                'id': iframe.get('id', ''),
                'name': iframe.get('name', ''),
                'title': iframe.get('title', ''),
                'suggested_locators': []
            }
            
            # Generate locators for the iframe
            if iframe.get('id'):
                iframe_info['suggested_locators'].append({
                    'type': 'ID',
                    'selector': f"#{iframe.get('id')}",
                    'stability': 'High'
                })
            
            if iframe.get('name'):
                iframe_info['suggested_locators'].append({
                    'type': 'Name',
                    'selector': f"[name='{iframe.get('name')}']",
                    'stability': 'Medium'
                })
            
            if iframe.get('src'):
                iframe_info['suggested_locators'].append({
                    'type': 'Src',
                    'selector': f"iframe[src='{iframe.get('src')}']",
                    'stability': 'Medium'
                })
            
            iframe_elements.append(iframe_info)
        
        return iframe_elements
    
    def generate_dynamic_locators(self, element) -> List[Dict[str, Any]]:
        """
        Generate locators that work well with dynamic content
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            List of dynamic-friendly locators
        """
        dynamic_locators = []
        
        # Partial text matching for dynamic content
        text_content = element.get_text(strip=True)
        if text_content and len(text_content) > 3:
            # XPath contains text
            dynamic_locators.append({
                'type': 'XPath Contains Text',
                'value': f"contains '{text_content[:20]}...'",
                'selector': f"//{element.name}[contains(text(), '{text_content[:20]}')]",
                'stability': 'Medium',
                'explanation': 'XPath with partial text matching - good for dynamic content'
            })
        
        # Partial attribute matching
        for attr, value in element.attrs.items():
            if isinstance(value, str) and len(value) > 5:
                dynamic_locators.append({
                    'type': 'XPath Contains Attribute',
                    'value': f"{attr} contains '{value[:10]}...'",
                    'selector': f"//{element.name}[contains(@{attr}, '{value[:10]}')]",
                    'stability': 'Medium',
                    'explanation': f'XPath with partial {attr} matching'
                })
        
        # Position-based with context
        if element.parent:
            parent_id = element.parent.get('id')
            if parent_id:
                dynamic_locators.append({
                    'type': 'XPath Parent Context',
                    'value': f"child of #{parent_id}",
                    'selector': f"//*[@id='{parent_id}']//{element.name}",
                    'stability': 'Medium',
                    'explanation': 'XPath using parent context for dynamic content'
                })
        
        return dynamic_locators
    
    def analyze_element_stability(self, element) -> Dict[str, Any]:
        """
        Analyze the stability characteristics of an element
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Stability analysis dictionary
        """
        stability_analysis = {
            'element_tag': element.name,
            'has_id': bool(element.get('id')),
            'has_data_test': bool(element.get('data-test')),
            'has_name': bool(element.get('name')),
            'has_stable_classes': False,
            'has_dynamic_content': False,
            'stability_score': 0,
            'recommendations': []
        }
        
        # Check for stable class names
        if element.get('class'):
            classes = element.get('class')
            stable_indicators = ['btn', 'form', 'input', 'container', 'wrapper']
            if any(indicator in ' '.join(classes) for indicator in stable_indicators):
                stability_analysis['has_stable_classes'] = True
        
        # Check for dynamic content indicators
        text_content = element.get_text(strip=True)
        dynamic_indicators = ['loading', 'spinner', 'dynamic', 'temp', 'placeholder']
        if any(indicator in text_content.lower() for indicator in dynamic_indicators):
            stability_analysis['has_dynamic_content'] = True
        
        # Calculate stability score
        score = 0
        if stability_analysis['has_id']:
            score += 3
        if stability_analysis['has_data_test']:
            score += 3
        if stability_analysis['has_name']:
            score += 2
        if stability_analysis['has_stable_classes']:
            score += 1
        if stability_analysis['has_dynamic_content']:
            score -= 2
        
        stability_analysis['stability_score'] = max(0, score)
        
        # Generate recommendations
        if not stability_analysis['has_id']:
            stability_analysis['recommendations'].append('Add an ID attribute for better stability')
        if not stability_analysis['has_data_test']:
            stability_analysis['recommendations'].append('Add a data-test attribute for testing')
        if stability_analysis['has_dynamic_content']:
            stability_analysis['recommendations'].append('Consider using more stable attributes instead of dynamic content')
        
        return stability_analysis


def demo():
    """Comprehensive demo of the enhanced locator generator with ALL elements and priority suggestions"""
    
    # Sample HTML with various element types
    sample_html = """
    <html>
        <head><title>E-commerce Product Page</title></head>
        <body>
            <div class="container">
                <h1>Premium Wireless Headphones</h1>
                <nav class="breadcrumb">
                    <a href="/">Home</a> > <a href="/electronics">Electronics</a> > <span>Headphones</span>
                </nav>
                
                <!-- Standard form elements -->
                <form id="login-form" class="auth-form">
                    <input type="text" name="username" placeholder="Username" data-test="username-input" class="form-input">
                    <input type="password" name="password" placeholder="Password" data-test="password-input" class="form-input">
                    <button id="login-btn" class="btn btn-primary" data-test="login-button" type="submit">
                        Login
                    </button>
                </form>
                
                <!-- Links and navigation -->
                <a href="/register" data-testid="register-link" class="signup-link">Create Account</a>
                
                <!-- Dynamic content elements -->
                <div class="dynamic-content">
                    <button class="help-btn" onclick="showHelp()">Help</button>
                    <span class="loading-spinner">Loading...</span>
                </div>
                
                <!-- Custom elements (potential shadow DOM) -->
                <my-custom-element data-test="custom-widget">
                    <div>Custom content</div>
                </my-custom-element>
                
                <!-- Iframe -->
                <iframe id="content-frame" src="/embed" name="main-frame" title="Main Content"></iframe>
                
                <!-- Elements with various attributes -->
                <div class="footer">
                    <button class="help-btn" onclick="showHelp()">Help</button>
                    <input type="email" name="newsletter" placeholder="Subscribe to newsletter" data-test="newsletter-input">
                </div>
            </div>
        </body>
    </html>
    """
    
    print("🚀 COMPREHENSIVE Enhanced Locator Generator Demo")
    print("=" * 70)
    
    # Demo 1: Default configuration
    print("\n📍 DEMO 1: Default Configuration")
    print("-" * 50)
    generator = LocatorGenerator()
    
    locators = generator.generate_locators(sample_html)
    ranked_locators = generator.rank_locators(locators)
    
    print(f"✅ Found {len(ranked_locators)} locators with default config")
    
    # Demo 2: Custom configuration
    print("\n📍 DEMO 2: Custom Configuration (XPath only, high stability)")
    print("-" * 50)
    
    custom_config = {
        'include_basic_locators': False,
        'include_xpath_locators': True,
        'include_advanced_css': False,
        'include_dynamic_locators': False,
        'preferred_locator_types': ['XPath ID', 'XPath Data Attribute'],
        'min_stability_score': 2
    }
    
    custom_generator = LocatorGenerator(custom_config)
    custom_locators = custom_generator.generate_locators(sample_html)
    custom_ranked = custom_generator.rank_locators(custom_locators)
    
    print(f"✅ Found {len(custom_ranked)} locators with custom config")
    print("Top 3 XPath locators:")
    for i, locator in enumerate(custom_ranked[:3], 1):
        print(f"  {i}. {locator['type']} - {locator['selector']}")
    
    # Demo 3: Shadow DOM Detection
    print("\n📍 DEMO 3: Shadow DOM Detection")
    print("-" * 50)
    shadow_elements = generator.find_shadow_dom_elements(sample_html)
    
    if shadow_elements:
        print(f"✅ Found {len(shadow_elements)} potential shadow DOM elements:")
        for element in shadow_elements:
            print(f"  • {element['tag_name']} - {element['explanation']}")
    else:
        print("ℹ️ No shadow DOM elements detected")
    
    # Demo 4: Iframe Detection
    print("\n📍 DEMO 4: Iframe Detection")
    print("-" * 50)
    iframe_elements = generator.find_iframe_elements(sample_html)
    
    if iframe_elements:
        print(f"✅ Found {len(iframe_elements)} iframe elements:")
        for iframe in iframe_elements:
            print(f"  • ID: {iframe['id']}, Src: {iframe['src']}")
            print(f"    Suggested locators: {len(iframe['suggested_locators'])}")
    else:
        print("ℹ️ No iframe elements detected")
    
    # Demo 5: Stability Analysis
    print("\n📍 DEMO 5: Element Stability Analysis")
    print("-" * 50)
    
    # Analyze a few elements
    soup = BeautifulSoup(sample_html, 'html.parser')
    test_elements = soup.find_all(['button', 'input'])[:3]
    
    for element in test_elements:
        analysis = generator.analyze_element_stability(element)
        print(f"Element: {analysis['element_tag']}")
        print(f"  Stability Score: {analysis['stability_score']}")
        print(f"  Has ID: {analysis['has_id']}")
        print(f"  Has Data-test: {analysis['has_data_test']}")
        print(f"  Recommendations: {len(analysis['recommendations'])}")
        if analysis['recommendations']:
            for rec in analysis['recommendations']:
                print(f"    • {rec}")
    
    # Demo 6: Smart Suggestions
    print("\n📍 DEMO 6: Smart Suggestions")
    print("-" * 50)
    suggestions = generator.generate_smart_suggestions(ranked_locators)
    
    high_priority = [s for s in suggestions if s['priority'] == 'High']
    medium_priority = [s for s in suggestions if s['priority'] == 'Medium']
    
    print(f"🔴 High Priority: {len(high_priority)}")
    for suggestion in high_priority[:3]:
        print(f"  • {suggestion['message']}")
    
    print(f"🟡 Medium Priority: {len(medium_priority)}")
    for suggestion in medium_priority[:3]:
        print(f"  • {suggestion['message']}")
    
    # Demo 7: Export Formats
    print("\n📍 DEMO 7: Export Formats")
    print("-" * 50)
    
    # CSV Export
    csv_export = generator.export_locators(ranked_locators[:5], 'csv')
    print("✅ CSV Export (first 5 locators):")
    print(csv_export[:300] + "..." if len(csv_export) > 300 else csv_export)
    
    # Demo 8: Locator Validation
    print("\n📍 DEMO 8: Locator Validation")
    print("-" * 50)
    
    # Validate top 3 locators
    for i, locator in enumerate(ranked_locators[:3]):
        validation = generator.validate_locator(locator, sample_html)
        print(f"Locator {i+1} ({locator['type']}):")
        print(f"  Valid: {validation['is_valid']} | Unique: {validation['is_unique']} | Count: {validation['element_count']}")
    
    print("\n📍 DEMO 9: Enhanced Features - ALL Elements with Priority Suggestions")
    print("-" * 70)
    
    # Generate locators for ALL elements (not just interactive ones)
    all_locators = generator.generate_locators(sample_html)
    print(f"✅ Found {len(all_locators)} locators for ALL web elements")
    
    # Group locators by element name
    element_groups = {}
    for locator in all_locators:
        element_name = locator.get('element_name', f"element_{locator['element_index']}")
        if element_name not in element_groups:
            element_groups[element_name] = []
        element_groups[element_name].append(locator)
    
    print(f"✅ Found {len(element_groups)} unique elements with appropriate names")
    
    # Show examples of priority suggestions
    print("\n💡 Priority Suggestions Examples:")
    for i, (element_name, locators) in enumerate(list(element_groups.items())[:3]):
        print(f"\n  {i+1}. Element: {element_name}")
        for j, locator in enumerate(locators[:2]):  # Show first 2 locators per element
            print(f"     Locator {j+1} ({locator['type']}): {locator['selector']}")
            if 'suggestions' in locator:
                print(f"       🔴 High: {locator['suggestions']['High']}")
                print(f"       🟡 Medium: {locator['suggestions']['Medium']}")
                print(f"       🟢 Low: {locator['suggestions']['Low']}")
    
    print("\n\n🎉 COMPREHENSIVE Demo Complete!")
    print("=" * 70)
    print("🚀 ALL ENHANCED FEATURES DEMONSTRATED:")
    print("• ✅ Advanced XPath locator generation")
    print("• ✅ Enhanced CSS selector strategies") 
    print("• ✅ Configurable locator generation")
    print("• ✅ ALL web elements detection (not just interactive)")
    print("• ✅ Intelligent element naming based on context")
    print("• ✅ Priority-based suggestions (High/Medium/Low)")
    print("• ✅ Locator ranking and scoring system")
    print("• ✅ Smart suggestions and recommendations")
    print("• ✅ Multiple export formats (JSON, CSV, Selenium, Playwright)")
    print("• ✅ Locator validation and testing")
    print("• ✅ Shadow DOM element detection")
    print("• ✅ Iframe element detection and analysis")
    print("• ✅ Dynamic content locator generation")
    print("• ✅ Element stability analysis")
    print("• ✅ Custom configuration system")
    print("• ✅ Comprehensive element detection")


if __name__ == "__main__":
    demo()
