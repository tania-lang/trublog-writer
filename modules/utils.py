"""
Utility Functions Module
========================

Handles:
- Session state management
- Export functions (CSV, JSON)
- Helper functions
"""

import streamlit as st
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime
import io


def init_session_state():
    """Initialize Streamlit session state variables"""
    
    defaults = {
        # API
        'api_key': '',
        
        # Company info
        'my_company_name': '',
        'my_company_domain': '',
        'my_additional_domains': '',
        'competitor_names': '',
        'additional_keywords': '',
        
        # Data
        'my_urls': [],
        'competitor_urls': {},
        'competitor_domains': {},
        'company_style': {},
        'link_map': {},
        'product_context': {},
        
        # Keywords
        'gap_analysis': [],
        'competitor_keywords': {},
        'my_keywords': set(),
        'selected_keywords': [],
        
        # Blogs
        'generated_blogs': [],
        
        # Settings
        'min_word_count': 2500,
        'min_competitor_frequency': 2,
        'max_blogs': 10
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def export_to_json(blogs: List[Dict]) -> str:
    """
    Export blogs to JSON format
    
    Args:
        blogs: List of blog dicts
        
    Returns:
        JSON string
    """
    export_data = {
        'generated_at': datetime.now().isoformat(),
        'total_blogs': len(blogs),
        'blogs': []
    }
    
    for blog in blogs:
        export_data['blogs'].append({
            'keyword': blog.get('keyword', ''),
            'type': blog.get('type', ''),
            'title': blog.get('title', ''),
            'meta_description': blog.get('meta_description', ''),
            'content': blog.get('content', ''),
            'word_count': blog.get('word_count', 0)
        })
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_to_csv(blogs: List[Dict]) -> str:
    """
    Export blogs to CSV format
    
    Args:
        blogs: List of blog dicts
        
    Returns:
        CSV string
    """
    rows = []
    
    for blog in blogs:
        rows.append({
            'Keyword': blog.get('keyword', ''),
            'Type': blog.get('type', ''),
            'Title': blog.get('title', ''),
            'Meta Description': blog.get('meta_description', ''),
            'Content': blog.get('content', ''),
            'Word Count': blog.get('word_count', 0),
            'Generated At': datetime.now().isoformat()
        })
    
    df = pd.DataFrame(rows)
    
    # Use StringIO for CSV export
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def clean_url(url: str) -> str:
    """Clean and normalize a URL"""
    url = url.strip()
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Add https if no protocol
    if not url.startswith('http'):
        url = 'https://' + url
    
    return url


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain


def is_valid_keyword(keyword: str) -> bool:
    """
    Basic validation for keyword quality
    
    Args:
        keyword: Keyword string
        
    Returns:
        True if valid
    """
    if not keyword:
        return False
    
    # Must be at least 2 words
    words = keyword.split()
    if len(words) < 2:
        return False
    
    # Must have at least 5 characters
    if len(keyword) < 5:
        return False
    
    # Must contain vowels (basic English check)
    if not any(c in keyword.lower() for c in 'aeiou'):
        return False
    
    # Check for common invalid patterns
    invalid_patterns = [
        r'^[a-z]{1,2}$',  # Single/double letters
        r'^[a-z]{2}-[a-z]{2}$',  # Language codes
        r'^\d+$',  # Pure numbers
        r'^(null|undefined|error|test)$',
    ]
    
    import re
    for pattern in invalid_patterns:
        if re.match(pattern, keyword.lower()):
            return False
    
    return True


def get_current_year() -> int:
    """Get current year"""
    return datetime.now().year


def calculate_priority(
    frequency: int,
    competitor_count: int,
    base_score: int
) -> int:
    """
    Calculate keyword priority score
    
    Formula: (frequency * 3) + (competitor_count * 5) + base_score
    
    Args:
        frequency: How often keyword appears
        competitor_count: Number of competitors with this keyword
        base_score: Base relevance score
        
    Returns:
        Priority score
    """
    return (frequency * 3) + (competitor_count * 5) + base_score
