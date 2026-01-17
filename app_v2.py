"""
SEO Blog Generator V2 - Improved & Beautiful
=============================================

Fixes:
1. Better keyword selection UI
2. Clear priority score explanation
3. Show gaps clearly (what Trupeer has vs doesn't have)
4. Auto-fetch domain from company name
5. CSV + Notion export
6. English-only internal links
7. Better blog structure learning
8. Beautiful UI in Trupeer colors

Run with: streamlit run app_v2.py
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()  # Load .env file for local development
from datetime import datetime
import json
import time
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import anthropic
import zipfile
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ============================================
# PAGE CONFIG & STYLING
# ============================================

st.set_page_config(
    page_title="TruBlog Writer | Trupeer",
    page_icon="✨",
    layout="wide"
)

# Trupeer color scheme - Primary #6366F1 (Indigo), Secondary #8B5CF6 (Purple), Accent #707be5
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Clean white background for main content */
    .stApp {
        background: #fafafa;
    }

    /* Main container - add padding */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* Sidebar - Trupeer dark purple gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] input::placeholder {
        color: rgba(255,255,255,0.6) !important;
    }

    /* Headers - dark purple, clear hierarchy */
    h1 {
        color: #1e1b4b !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    h2 {
        color: #312e81 !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }
    h3 {
        color: #4338ca !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* Body text - dark gray for readability */
    p, span, div, label {
        color: #1f2937 !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Primary buttons - Trupeer gradient */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary buttons */
    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]) {
        background: white !important;
        color: #6366F1 !important;
        border: 2px solid #6366F1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #f5f3ff !important;
    }

    /* Tabs - clean design with readable text */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        padding: 4px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        color: #374151 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #1f2937 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
        color: #ffffff !important;
        border-radius: 8px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] * {
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span {
        color: inherit !important;
    }

    /* Metrics - larger, clearer */
    [data-testid="stMetricValue"] {
        color: #6366F1 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    /* Input fields - clean borders */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stNumberInput input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 0.6rem !important;
        font-size: 0.95rem !important;
        color: #1f2937 !important;
        background: white !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    /* Number input specific */
    .stNumberInput > div > div > input {
        color: #1f2937 !important;
        background: white !important;
    }

    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* Data editor / tables */
    [data-testid="stDataFrame"],
    .stDataFrame {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] th {
        background: #f8fafc !important;
        color: #1e1b4b !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    [data-testid="stDataFrame"] td {
        color: #1f2937 !important;
        padding: 10px 12px !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: #f8fafc !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1e1b4b !important;
    }
    .streamlit-expanderContent {
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
    }

    /* Success/Warning/Error messages */
    .stSuccess {
        background: #ecfdf5 !important;
        border-left: 4px solid #10b981 !important;
        color: #065f46 !important;
    }
    .stWarning {
        background: #fffbeb !important;
        border-left: 4px solid #f59e0b !important;
        color: #92400e !important;
    }
    .stError {
        background: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        color: #991b1b !important;
    }
    .stInfo {
        background: #eff6ff !important;
        border-left: 4px solid #6366F1 !important;
        color: #1e40af !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
        border-radius: 4px !important;
    }

    /* Checkbox */
    .stCheckbox label span {
        color: #374151 !important;
    }

    /* Code blocks */
    code {
        background: #f1f5f9 !important;
        color: #6366F1 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }
    pre {
        background: #1e1b4b !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    pre code {
        color: #e0e7ff !important;
        background: transparent !important;
    }

    /* Dividers */
    hr {
        border: none !important;
        border-top: 1px solid #e2e8f0 !important;
        margin: 1.5rem 0 !important;
    }

    /* Caption text */
    .stCaption, small {
        color: #64748b !important;
        font-size: 0.85rem !important;
    }

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background: #6366F1 !important;
        color: white !important;
        border-radius: 6px !important;
    }

    /* Number input */
    .stNumberInput input {
        text-align: center !important;
    }

    /* Custom success box */
    .success-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-left: 4px solid #10b981;
        padding: 1rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .success-box strong {
        color: #065f46;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #6366F1 !important;
    }

    /* Selectbox dropdown - ensure readable text */
    [data-baseweb="select"] {
        border-radius: 8px !important;
    }
    [data-baseweb="select"] > div {
        background: white !important;
        color: #1f2937 !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div[class*="valueContainer"] {
        color: #1f2937 !important;
    }
    [data-baseweb="popover"] {
        border-radius: 8px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        background: white !important;
    }
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="option"] {
        color: #1f2937 !important;
        background: white !important;
    }
    [role="option"]:hover,
    [data-baseweb="menu"] li:hover {
        background: #f1f5f9 !important;
    }
    .stSelectbox [data-baseweb="select"] * {
        color: #1f2937 !important;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZE SESSION STATE
# ============================================

# ============================================
# CONTENT TYPE DEFINITIONS
# ============================================

CONTENT_TYPES = {
    'blog': {
        'name': 'Blog Post',
        'description': 'Educational/informational content that builds authority and drives organic traffic',
        'structure': '''
# [Compelling Title with Primary Keyword]

[Hook paragraph - problem/question that resonates]

[Context - why this matters to the reader]

## [H2: First Main Point]
[3-4 paragraphs with examples, data, insights]

## [H2: Second Main Point]
[Detailed content with practical value]

## [H2: Third Main Point]
[More depth with real-world applications]

## Key Takeaways
[Bulleted summary of main points]

## FAQ
[5 relevant questions and answers]

[Soft CTA to related content or product]
'''
    },
    'listicle': {
        'name': 'Listicle',
        'description': 'List-based article (e.g., "Top 10 Tools for...") - scannable, high engagement',
        'structure': '''
# [Number] Best [Topic] in [Year] (+ Our Top Pick)

[Brief 2-3 sentence intro - what reader will learn]

**Quick Summary Table:**
| Tool | Best For | Price |
|------|----------|-------|

## 1. [First Item] - Best for [Use Case]
**Key Features:**
- Feature 1
- Feature 2

**Pros:** [2-3 pros]
**Cons:** [1-2 cons]
**Pricing:** [Price info]

[Repeat for each item...]

## How We Evaluated These [Items]
[Brief methodology]

## Conclusion: Which [Item] Should You Choose?
[Recommendation based on use cases]
'''
    },
    'tool_page': {
        'name': 'Tool/Product Page',
        'description': 'Product-focused page highlighting features, benefits, and use cases',
        'structure': '''
# [Product Name]: [Primary Benefit Statement]

[Hero section - what the tool does in one compelling sentence]

## Why Teams Choose [Product]
[3 key differentiators with brief explanations]

## Key Features
### [Feature 1 Name]
[Description + benefit to user]

### [Feature 2 Name]
[Description + benefit to user]

### [Feature 3 Name]
[Description + benefit to user]

## Use Cases
- **[Use Case 1]:** How [Product] helps
- **[Use Case 2]:** How [Product] helps
- **[Use Case 3]:** How [Product] helps

## How It Works
1. [Step 1]
2. [Step 2]
3. [Step 3]

## What Customers Say
[Testimonial or social proof]

## Get Started with [Product]
[Clear CTA with next steps]
'''
    },
    'solution_page': {
        'name': 'Solution Page',
        'description': 'Problem/solution focused landing page targeting specific pain points',
        'structure': '''
# [Solution] for [Target Audience/Problem]

[Pain point statement - "Struggling with X?"]

## The Challenge
[Describe the problem in detail - make reader feel understood]

## The Solution: [Product/Approach Name]
[How your solution addresses the pain point]

## Benefits
### [Benefit 1]
[Explanation with proof point]

### [Benefit 2]
[Explanation with proof point]

### [Benefit 3]
[Explanation with proof point]

## How [Company] Helps You [Achieve Goal]
[Specific capabilities mapped to the solution]

## Results You Can Expect
[Metrics, outcomes, or transformations]

## Success Story
[Brief case study or example]

## Ready to [Desired Outcome]?
[Strong CTA with clear next step]
'''
    },
    'comparison': {
        'name': 'Comparison Page',
        'description': 'X vs Y comparison helping readers make decisions',
        'structure': '''
# [Product A] vs [Product B]: [Year] Comparison

[Intro - what you'll compare and why it matters]

## Quick Verdict
[TL;DR for scanners - who should choose which]

## Comparison Overview
| Feature | [Product A] | [Product B] | Winner |
|---------|-------------|-------------|--------|

## [Product A] Overview
[What it is, who it's for, key strengths]

## [Product B] Overview
[What it is, who it's for, key strengths]

## Feature Comparison

### [Feature Category 1]
**[Product A]:** [Details]
**[Product B]:** [Details]
**Winner:** [Which and why]

### [Feature Category 2]
[Same format...]

## Pricing Comparison
[Detailed pricing breakdown]

## Pros and Cons

### [Product A]
**Pros:** [List]
**Cons:** [List]

### [Product B]
**Pros:** [List]
**Cons:** [List]

## Which Should You Choose?
- Choose [Product A] if...
- Choose [Product B] if...

## FAQ
[Common comparison questions]
'''
    },
    'alternative': {
        'name': 'Alternative Page',
        'description': 'Best alternatives to X - targets users looking for options',
        'structure': '''
# [Number] Best [Product X] Alternatives in [Year]

[Why people look for alternatives - common pain points]

## Quick Comparison
| Alternative | Best For | Price | Rating |
|-------------|----------|-------|--------|

## Why Look for [Product X] Alternatives?
[Common reasons - pricing, features, support, etc.]

## Top [Product X] Alternatives

### 1. [Alternative 1] - Best Overall Alternative
[Overview]
**Key Features:** [List]
**Pricing:** [Details]
**Best For:** [Use case]

### 2. [Alternative 2] - Best for [Specific Use]
[Same format...]

[Continue for each alternative...]

## How to Choose the Right Alternative
[Decision criteria and recommendations]

## Making the Switch
[Tips for migration/transition]

## Conclusion
[Summary and top recommendation]
'''
    },
    'how_to': {
        'name': 'How-To Guide',
        'description': 'Step-by-step tutorial teaching readers to accomplish a specific task',
        'structure': '''
# How to [Accomplish Task]: [Benefit/Outcome]

[Brief intro - what reader will learn and achieve]

## What You'll Need
- [Prerequisite 1]
- [Prerequisite 2]
- [Tool/Resource needed]

## Quick Steps Overview
1. [Step 1 summary]
2. [Step 2 summary]
3. [Step 3 summary]

## Step 1: [Action Verb + Task]
[Detailed instructions]
[Screenshot/visual if applicable]
**Pro Tip:** [Helpful hint]

## Step 2: [Action Verb + Task]
[Detailed instructions]
[Screenshot/visual if applicable]

## Step 3: [Action Verb + Task]
[Detailed instructions]

[Continue for all steps...]

## Common Mistakes to Avoid
- [Mistake 1 and how to avoid]
- [Mistake 2 and how to avoid]

## Troubleshooting
**Problem:** [Common issue]
**Solution:** [How to fix]

## Next Steps
[What to do after completing this guide]

## FAQ
[Related questions]
'''
    }
}


def init_state():
    defaults = {
        'api_key': os.environ.get('ANTHROPIC_API_KEY', ''),
        'my_company_name': '',
        'my_company_domain': '',
        'competitor_names': '',
        'my_urls': [],
        'my_keywords': set(),
        'competitor_data': {},
        'all_keywords': {},
        'gap_keywords': [],
        'selected_keywords': [],
        'company_style': {},
        'content_structures': {},  # Learned structures for each content type
        'sample_urls': {},  # User-provided sample URLs
        'link_map': {},
        'generated_blogs': [],
        'analysis_done': False,
        'total_cost': 0.0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ============================================
# API CLIENT
# ============================================

class APIClient:
    HAIKU = 'claude-3-haiku-20240307'
    SONNET = 'claude-sonnet-4-20250514'
    
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cost = 0.0
    
    def call(self, prompt, model="haiku", max_tokens=1000):
        model_id = self.HAIKU if model == "haiku" else self.SONNET
        
        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Track cost
        input_cost = response.usage.input_tokens * (0.25 if model == "haiku" else 3.0) / 1_000_000
        output_cost = response.usage.output_tokens * (1.25 if model == "haiku" else 15.0) / 1_000_000
        self.cost += input_cost + output_cost
        
        return response.content[0].text

# ============================================
# STRUCTURE LEARNING FUNCTIONS
# ============================================

def learn_structure_from_url(api_client, url, content_type=None):
    """
    Fetch a URL and learn its content structure using AI.
    Returns a structure template that can be used for content generation.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove non-content elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Extract structure
        structure_data = {
            'url': url,
            'title': '',
            'headings': [],
            'sections': [],
            'has_table': False,
            'has_list': False,
            'has_faq': False,
            'word_count': 0
        }

        # Get title
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            structure_data['title'] = title_tag.get_text(strip=True)

        # Get all headings with hierarchy
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            structure_data['headings'].append({
                'level': h.name,
                'text': h.get_text(strip=True)[:100]
            })

        # Check for structural elements
        structure_data['has_table'] = len(soup.find_all('table')) > 0
        structure_data['has_list'] = len(soup.find_all(['ul', 'ol'])) > 0
        structure_data['has_faq'] = bool(soup.find(string=re.compile(r'FAQ|Frequently Asked', re.I)))

        # Get content text
        content = soup.get_text(' ', strip=True)
        structure_data['word_count'] = len(content.split())

        # Use AI to analyze and create structure template
        headings_text = "\n".join([f"{h['level']}: {h['text']}" for h in structure_data['headings'][:15]])

        prompt = f"""Analyze this page structure and create a reusable content template.

URL: {url}
Title: {structure_data['title']}
Has Table: {structure_data['has_table']}
Has Lists: {structure_data['has_list']}
Has FAQ: {structure_data['has_faq']}
Word Count: ~{structure_data['word_count']}

HEADINGS STRUCTURE:
{headings_text}

Create a markdown template showing:
1. The heading structure pattern (H1, H2, H3 hierarchy)
2. What type of content goes in each section (in brackets)
3. Special elements like tables, lists, CTAs

Return ONLY the template in markdown format. Use [brackets] for content descriptions.
Example:
# [Main Title with Keyword]
[Intro paragraph]
## [First Major Topic]
[2-3 paragraphs]
### [Subtopic]
[Details]
"""

        template = api_client.call(prompt, model="haiku", max_tokens=800)
        return {
            'url': url,
            'template': template.strip(),
            'metadata': structure_data
        }

    except Exception as e:
        return None


def learn_structures_from_company(api_client, urls, company_name):
    """
    Learn different content structures from a company's existing pages.
    Identifies and categorizes different content types automatically.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    learned_structures = {}

    # Categorize URLs by likely content type
    categorized = {
        'blog': [],
        'listicle': [],
        'tool_page': [],
        'solution_page': [],
        'comparison': [],
        'alternative': [],
        'how_to': []
    }

    for url_data in urls[:100]:  # Check first 100 URLs
        url = url_data['url'].lower()
        slug = url_data.get('slug', '').lower()

        if 'vs' in slug or 'versus' in slug or 'compare' in slug:
            categorized['comparison'].append(url_data)
        elif 'alternative' in slug:
            categorized['alternative'].append(url_data)
        elif 'how-to' in slug or 'tutorial' in slug or 'guide' in slug:
            categorized['how_to'].append(url_data)
        elif 'top-' in slug or 'best-' in slug or re.search(r'\d+-', slug):
            categorized['listicle'].append(url_data)
        elif '/product' in url or '/feature' in url or '/tool' in url:
            categorized['tool_page'].append(url_data)
        elif '/solution' in url or '/use-case' in url:
            categorized['solution_page'].append(url_data)
        elif '/blog/' in url or '/post/' in url or '/article/' in url:
            categorized['blog'].append(url_data)

    # Learn structure from one example of each type
    for content_type, type_urls in categorized.items():
        if type_urls:
            # Take first URL of this type
            sample_url = type_urls[0]['url']
            structure = learn_structure_from_url(api_client, sample_url, content_type)
            if structure:
                learned_structures[content_type] = structure

    return learned_structures


# ============================================
# HELPER FUNCTIONS
# ============================================

def find_domain_from_name(api_client, company_name):
    """Use Claude to intelligently find the correct domain for a company"""
    prompt = f"""Find the official website domain for the company/product "{company_name}".

Important: Many companies don't use simple .com domains. Examples:
- Scribe (documentation tool) = scribehow.com (NOT scribe.com)
- Notion = notion.so
- Figma = figma.com
- Loom = loom.com
- Canva = canva.com
- Synthesia = synthesia.io
- Guidde = guidde.com

Think about what type of product/company "{company_name}" is and find their ACTUAL official domain.

Return ONLY the exact domain (e.g., "scribehow.com"), nothing else. No explanation."""

    response = api_client.call(prompt, model="sonnet", max_tokens=50)

    # Clean response
    domain = response.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
    # Remove any trailing punctuation or text
    domain = domain.split()[0] if domain else ""
    domain = domain.rstrip('.,;:')

    return domain


def fetch_sitemap(domain, include_subdomains=True):
    """Fetch all URLs from a domain's sitemap - FAST with concurrent fetching"""

    # Clean domain
    domain = domain.replace('https://', '').replace('http://', '').strip('/')
    if domain.startswith('www.'):
        domain = domain[4:]

    urls = []
    urls_lock = threading.Lock()
    sitemaps_to_process = []

    # Try both www and non-www versions
    bases = [f"https://{domain}", f"https://www.{domain}"]

    # Common sitemap locations
    sitemap_paths = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/wp-sitemap.xml',
        '/sitemap/sitemap.xml',
        '/sitemaps/sitemap.xml',
        '/sitemap1.xml',
        '/post-sitemap.xml',
        '/page-sitemap.xml',
        '/blog-sitemap.xml',
        '/sitemap-posts.xml',
    ]

    # Build initial sitemap list
    for base in bases:
        for path in sitemap_paths:
            sitemaps_to_process.append(base + path)

    # Common subdomains to check
    subdomains = ['blog', 'www', 'help', 'support', 'docs', 'learn', 'resources', 'knowledge', 'community', 'kb', 'faq']

    if include_subdomains:
        for sub in subdomains:
            sub_base = f"https://{sub}.{domain}"
            sitemaps_to_process.append(f"{sub_base}/sitemap.xml")
            sitemaps_to_process.append(f"{sub_base}/sitemap_index.xml")

    # Check robots.txt for all variants (concurrently)
    robots_urls = [f"{base}/robots.txt" for base in bases]
    if include_subdomains:
        robots_urls.extend([f"https://{sub}.{domain}/robots.txt" for sub in subdomains[:5]])

    def fetch_robots(robots_url):
        """Fetch robots.txt and extract sitemap URLs"""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            })
            robots = session.get(robots_url, timeout=10, allow_redirects=True)
            if robots.status_code == 200:
                matches = re.findall(r'Sitemap:\s*(\S+)', robots.text, re.I)
                return [m.strip() for m in matches]
        except:
            pass
        return []

    # Fetch robots.txt files concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        robot_futures = {executor.submit(fetch_robots, url): url for url in robots_urls}
        for future in as_completed(robot_futures):
            found_sitemaps = future.result()
            sitemaps_to_process = found_sitemaps + sitemaps_to_process  # Priority

    processed = set()
    sitemap_queue = list(sitemaps_to_process)
    child_sitemaps = []  # Collect child sitemaps for batch processing
    max_sitemaps = 500

    def fetch_single_sitemap(sitemap_url):
        """Fetch a single sitemap and return URLs or child sitemaps"""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
            resp = session.get(sitemap_url, timeout=30, allow_redirects=True)
            if resp.status_code != 200:
                return {'type': 'empty', 'urls': [], 'children': []}

            content = resp.text

            # Handle sitemap index
            if '<sitemapindex' in content.lower():
                child_urls = re.findall(r'<loc>\s*([^<]+)\s*</loc>', content, re.I)
                return {'type': 'index', 'urls': [], 'children': [c.strip() for c in child_urls]}

            # Extract page URLs
            page_urls = re.findall(r'<loc>\s*([^<]+)\s*</loc>', content, re.I)
            extracted = []
            for url in page_urls:
                url = url.strip()
                if '.xml' in url.lower():
                    continue
                skip_patterns = ['/tag/', '/category/', '/author/', '/page/', '/feed/',
                                '/wp-admin/', '/wp-content/', '/wp-includes/', '/cart/',
                                '/checkout/', '/my-account/', '/cdn-cgi/', '/.well-known/']
                if any(p in url.lower() for p in skip_patterns):
                    continue
                if is_non_english_url(url):
                    continue
                slug = re.sub(r'https?://[^/]+', '', url).split('?')[0]
                extracted.append({'url': url, 'slug': slug, 'domain': domain})

            return {'type': 'sitemap', 'urls': extracted, 'children': []}
        except:
            return {'type': 'error', 'urls': [], 'children': []}

    # Process sitemaps in batches with concurrency
    while sitemap_queue and len(processed) < max_sitemaps:
        # Get batch of sitemaps to process
        batch = []
        while sitemap_queue and len(batch) < 30:
            sm = sitemap_queue.pop(0)
            if sm not in processed:
                processed.add(sm)
                batch.append(sm)

        if not batch:
            break

        # Fetch batch concurrently
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(fetch_single_sitemap, sm): sm for sm in batch}
            for future in as_completed(futures):
                result = future.result()
                if result['type'] == 'index':
                    # Add child sitemaps to front of queue
                    for child in result['children']:
                        if child not in processed:
                            sitemap_queue.insert(0, child)
                elif result['type'] == 'sitemap':
                    urls.extend(result['urls'])

        if len(urls) > 50000:
            break

    # Dedupe while preserving order
    seen = set()
    unique = []
    for u in urls:
        if u['url'] not in seen:
            seen.add(u['url'])
            unique.append(u)

    return unique


def is_non_english_url(url):
    """Check if URL is non-English"""
    url_lower = url.lower()
    
    # Language patterns
    patterns = [
        '/pt/', '/br/', '/pt-br/', '/es/', '/de/', '/fr/', '/it/',
        '/ja/', '/jp/', '/ko/', '/zh/', '/cn/', '/ru/', '/ar/',
        '/nl/', '/pl/', '/tr/', '/sv/', '/da/', '/fi/',
        'lang=pt', 'lang=es', 'lang=de', 'lang=fr', 'locale='
    ]
    
    for p in patterns:
        if p in url_lower:
            return True
    
    return False


def fetch_page_content(url, session):
    """Fetch page and extract title, headings, meta description"""
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract title
        title = ''
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Also check H1
        h1_tag = soup.find('h1')
        h1 = h1_tag.get_text(strip=True) if h1_tag else ''

        # Extract meta description
        meta_desc = ''
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag and meta_tag.get('content'):
            meta_desc = meta_tag.get('content')

        # Extract H2 headings (main sections)
        h2s = [h.get_text(strip=True) for h in soup.find_all('h2')[:5]]

        return {
            'url': url,
            'title': title,
            'h1': h1,
            'meta_description': meta_desc,
            'h2s': h2s
        }
    except:
        return None


def extract_keyword_from_page(page_data):
    """Extract the main target keyword from page content using SEO best practices"""
    if not page_data:
        return None

    title = page_data.get('title', '') or page_data.get('h1', '')
    if not title:
        return None

    # Clean the title - remove site name suffix (e.g., "| Company Name", "- Company")
    title = re.split(r'\s*[\|\-–—]\s*(?=[A-Z])', title)[0].strip()

    # Skip non-content pages
    skip_patterns = ['home', 'contact', 'about us', 'privacy', 'terms', 'login',
                     'sign up', 'pricing', '404', 'error', 'cart', 'checkout']
    title_lower = title.lower()
    if any(p in title_lower for p in skip_patterns):
        return None

    # Skip very short or very long titles
    if len(title) < 10 or len(title) > 150:
        return None

    # Determine content type from title patterns
    kw_type = 'Blog'
    title_lower = title.lower()

    if any(x in title_lower for x in [' vs ', ' vs.', ' versus ', ' compared to ']):
        kw_type = 'Comparison'
    elif any(x in title_lower for x in ['alternative', 'alternatives to', 'competitor']):
        kw_type = 'Alternative'
    elif any(x in title_lower for x in ['how to ', 'guide to ', 'tutorial', 'step by step', 'steps to']):
        kw_type = 'How-To'
    elif any(x in title_lower for x in ['best ', 'top ', ' tools', ' software', ' apps']):
        kw_type = 'Listicle'
    elif any(x in title_lower for x in ['what is ', 'what are ', 'definition', 'meaning of']):
        kw_type = 'Educational'

    return {
        'keyword': title,
        'type': kw_type,
        'meta_description': page_data.get('meta_description', ''),
        'url': page_data.get('url', '')
    }


def extract_keywords_from_urls(urls, max_pages=200):
    """Extract keywords from URLs - uses slug analysis (fast) with improved detection"""

    keywords = []

    # Filter to content pages
    high_priority = []
    medium_priority = []
    low_priority = []

    for url_data in urls:
        url = url_data['url'].lower()
        slug = url_data.get('slug', '').lower()

        # Skip non-content pages
        skip_patterns = ['/tag/', '/category/', '/author/', '/page/', '/cart/',
                        '/checkout/', '/account/', '/login', '/signup', '/privacy',
                        '/terms', '/contact', '/about-us', '/careers', '/press',
                        '/wp-admin', '/wp-content', '/assets/', '/static/', '/cdn/',
                        '/favicon', '/robots', '/sitemap', '.xml', '.json', '.css', '.js']
        if any(p in url for p in skip_patterns):
            continue

        # High priority: explicit content paths
        high_content = ['/blog/', '/post/', '/article/', '/resource/', '/guide/',
                        '/learn/', '/how-to/', '/tutorial/', '/comparison/',
                        '/alternative/', '/vs-', '-vs-', '/help/', '/docs/',
                        '/knowledge/', '/library/', '/insights/', '/tips/',
                        '/solutions/', '/products/', '/features/', '/tools/']
        if any(p in url for p in high_content):
            high_priority.append(url_data)
            continue

        # High priority: slug patterns indicating content
        slug_content = ['how-to', 'guide', 'tutorial', 'best-', 'top-', '-vs-',
                       'alternative', 'comparison', 'review', 'tips', 'what-is',
                       'create-', 'make-', 'build-', 'use-', '-tool', '-software',
                       '-generator', '-maker', '-creator', '-builder', '-free',
                       '-online', 'screen-record', 'video-', '-demo', '-template']
        if any(p in slug for p in slug_content):
            high_priority.append(url_data)
            continue

        # Medium priority: has a meaningful slug path
        last_part = slug.rstrip('/').split('/')[-1] if slug else ''
        if last_part and len(last_part) > 8 and '-' in last_part:
            medium_priority.append(url_data)
        elif len(slug) > 5:
            low_priority.append(url_data)

    # Combine with priority order
    content_urls = high_priority + medium_priority + low_priority

    # Process URLs (limit to max_pages)
    urls_to_process = content_urls[:max_pages]

    for url_data in urls_to_process:
        slug = url_data.get('slug', '')
        url = url_data.get('url', '')

        # Extract keyword from slug (fast, reliable)
        kw_data = extract_keyword_from_slug(slug)

        if kw_data and kw_data.get('keyword'):
            kw_data['url'] = url
            keywords.append(kw_data)

    return keywords


def extract_keywords_from_urls_with_content(urls, max_pages=30):
    """Extract keywords by fetching actual page content - slower but more accurate"""

    keywords = []
    keywords_lock = threading.Lock()

    # Filter to likely content pages
    content_urls = []

    for url_data in urls:
        url = url_data['url'].lower()
        if any(p in url for p in ['/blog/', '/post/', '/article/', '/resource/',
                                   '/guide/', '/learn/', '/help/', '/docs/']):
            content_urls.append(url_data)

    urls_to_fetch = content_urls[:max_pages]

    def fetch_and_extract(url_data):
        """Fetch a single page and extract keyword"""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            })
            page_content = fetch_page_content(url_data['url'], session)
            if page_content:
                keyword_data = extract_keyword_from_page(page_content)
                if keyword_data:
                    return keyword_data
        except:
            pass
        # Fallback to slug
        return extract_keyword_from_slug(url_data.get('slug', ''))

    # Use ThreadPoolExecutor for concurrent fetching
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_and_extract, url_data): url_data for url_data in urls_to_fetch}

        for future in as_completed(futures):
            result = future.result()
            if result and result.get('keyword'):
                with keywords_lock:
                    keywords.append(result)

    return keywords


def extract_keyword_from_slug(slug):
    """Extract keyword from URL slug - improved for better results"""
    if not slug or slug == '/' or len(slug) < 3:
        return None

    slug = slug.lower().strip('/')
    parts = slug.split('/')

    # Skip non-content paths
    skip_paths = {'tag', 'category', 'author', 'page', 'wp-content', 'assets',
                  'static', 'images', 'img', 'css', 'js', 'api', 'admin', 'login',
                  'search', 'feed', 'rss', 'sitemap', 'robots', 'favicon', 'cdn',
                  'media', 'uploads', 'files', 'download', 'attachment'}
    for part in parts:
        if part in skip_paths:
            return None

    # Get the last meaningful part (usually the article slug)
    best_part = None
    for part in reversed(parts):
        if len(part) < 3 or len(part) > 80:
            continue
        # Skip hash/ID-like parts
        if re.search(r'^[a-z0-9]{20,}$', part):
            continue
        # Skip mostly numeric parts
        if sum(c.isdigit() for c in part) > len(part) * 0.4:
            continue
        best_part = part
        break

    if not best_part:
        return None

    # Split on hyphens/underscores
    words = re.split(r'[-_]', best_part)

    # Minimal stop words - keep more meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                  'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}

    clean_words = []
    for w in words:
        # Accept words 2+ chars (allows "ai", "vs", etc)
        if len(w) >= 2 and w.isalpha() and w not in stop_words:
            clean_words.append(w)

    # Accept single meaningful words if they're long enough or domain-relevant
    valuable_single = {'generator', 'alternative', 'comparison', 'tutorial', 'guide',
                       'software', 'tool', 'review', 'template', 'recorder', 'maker',
                       'creator', 'builder', 'editor', 'converter', 'downloader'}

    if len(clean_words) == 0:
        return None
    elif len(clean_words) == 1:
        # Only accept single words if they're valuable or long
        if clean_words[0] not in valuable_single and len(clean_words[0]) < 8:
            return None

    # Take up to 6 words for better context
    clean_words = clean_words[:6]
    keyword = ' '.join(clean_words)

    # Less strict vowel check
    vowel_count = sum(1 for c in keyword if c in 'aeiou')
    if vowel_count < len(keyword.replace(' ', '')) * 0.1:
        return None

    # Determine type based on keywords
    kw_type = 'Blog'
    word_set = set(clean_words)
    keyword_lower = keyword.lower()

    if word_set & {'alternative', 'alternatives', 'competitor', 'competitors'}:
        kw_type = 'Alternative'
    elif word_set & {'comparison', 'compare'} or ' vs ' in keyword_lower or keyword_lower.endswith(' vs'):
        kw_type = 'Comparison'
    elif word_set & {'generator', 'creator', 'maker', 'builder', 'tool', 'software', 'app', 'free', 'online', 'recorder', 'editor'}:
        kw_type = 'Tool'
    elif word_set & {'tutorial', 'guide', 'learn', 'create', 'make', 'build', 'step', 'how'}:
        kw_type = 'How-To'
    elif word_set & {'best', 'top', 'list'}:
        kw_type = 'Listicle'

    return {
        'keyword': ' '.join(w.capitalize() for w in clean_words),
        'type': kw_type
    }


def calculate_priority(occurrence_count):
    """
    Simple priority score = total occurrences across competitor slugs

    The more times a keyword appears across competitor URLs, the higher priority.
    """
    return occurrence_count


def intelligent_keyword_filter(api_client, raw_keywords, company_name, company_description=None):
    """
    Use Claude to intelligently filter and refine keywords - FAST version.
    - Removes generic/non-SEO titles
    - Extracts actual search keywords
    - Scores relevance to company's business
    """
    if not raw_keywords:
        return []

    # Batch keywords for efficiency (process 100 at a time for speed)
    batch_size = 100
    all_refined = []

    # Auto-detect company description if not provided
    if not company_description:
        company_description = f"{company_name} is a video creation and screen recording tool for creating tutorials, product demos, training videos, and documentation."

    # Limit total keywords to process (top 300 by frequency)
    sorted_keywords = sorted(raw_keywords, key=lambda x: x.get('frequency', 0), reverse=True)[:300]

    for i in range(0, len(sorted_keywords), batch_size):
        batch = sorted_keywords[i:i + batch_size]

        # Format keywords for prompt
        kw_list = "\n".join([f"{j+1}. {kw.get('keyword', '')} (Type: {kw.get('type', 'Blog')})"
                            for j, kw in enumerate(batch)])

        prompt = f"""You are an SEO expert. Analyze these page titles/keywords from competitor websites and filter them for {company_name}.

COMPANY CONTEXT:
{company_description}

RAW KEYWORDS FROM COMPETITORS:
{kw_list}

YOUR TASK:
1. FILTER OUT non-valuable keywords:
   - Generic product pages ("Pricing", "About Us", "Contact")
   - Login/signup pages
   - Legal pages (Privacy Policy, Terms)
   - News/press releases unless industry-relevant
   - Very brand-specific pages that can't be adapted

2. EXTRACT the actual SEO keyword people would search for:
   - "How to Create a Screen Recording in 2024 | Loom" → "how to create a screen recording"
   - "Best Video Editing Software for Beginners - Guide" → "best video editing software for beginners"
   - "Loom vs Vidyard: Complete Comparison" → "loom vs vidyard"

3. SCORE relevance to {company_name} (1-10):
   - 10: Directly relevant (screen recording, video tutorials, product demos)
   - 7-9: Related (documentation, training, onboarding)
   - 4-6: Tangentially related (productivity, communication)
   - 1-3: Not very relevant

Return JSON array only (no other text):
[
  {{"original": "original title", "keyword": "extracted seo keyword", "type": "Comparison|Alternative|How-To|Listicle|Educational|Tool", "relevance": 8, "reason": "brief reason"}},
  ...
]

Only include keywords with relevance >= 5. Return empty array [] if none qualify."""

        try:
            response = api_client.call(prompt, model="haiku", max_tokens=2000)

            # Parse JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                refined = json.loads(json_match.group())
                for item in refined:
                    if item.get('relevance', 0) >= 5:
                        all_refined.append({
                            'keyword': item.get('keyword', '').title(),
                            'type': item.get('type', 'Blog'),
                            'relevance': item.get('relevance', 5),
                            'reason': item.get('reason', ''),
                            'original': item.get('original', '')
                        })
        except Exception as e:
            # On error, keep original keywords with basic filtering
            for kw in batch:
                keyword = kw.get('keyword', '')
                if len(keyword) > 15 and not any(skip in keyword.lower() for skip in
                    ['privacy', 'terms', 'login', 'signup', 'pricing', 'contact', 'about us']):
                    all_refined.append({
                        'keyword': keyword,
                        'type': kw.get('type', 'Blog'),
                        'relevance': 5,
                        'reason': 'Auto-included',
                        'original': keyword
                    })

    return all_refined


def adapt_keyword_for_trupeer(api_client, keyword, keyword_type, company_name, company_description=""):
    """
    Adapt a competitor keyword to be Trupeer-focused.
    E.g., "Loom vs Vidyard" → "Trupeer vs Loom vs Vidyard" or focus on Trupeer's strengths
    """
    prompt = f"""You are an SEO strategist for {company_name}.

COMPANY CONTEXT:
{company_description}

ORIGINAL KEYWORD: {keyword}
KEYWORD TYPE: {keyword_type}

Adapt this keyword for {company_name}'s blog. Consider:
1. If it's a comparison (X vs Y), should {company_name} be included?
2. If it's an alternative post, make it about {company_name} as the alternative
3. If it's a how-to, focus on how to do it with {company_name} or in general
4. If it's a listicle, ensure {company_name} would naturally fit

Return JSON only:
{{
  "adapted_keyword": "the keyword to target",
  "blog_angle": "brief description of how to angle the blog for {company_name}",
  "include_company_in_title": true/false,
  "comparison_products": ["list", "of", "products to compare if applicable"]
}}"""

    try:
        response = api_client.call(prompt, model="haiku", max_tokens=500)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "adapted_keyword": keyword,
        "blog_angle": f"Write about {keyword} highlighting {company_name}'s capabilities",
        "include_company_in_title": False,
        "comparison_products": []
    }


def learn_company_context(api_client, urls, company_name):
    """
    Learn what the company does from their website pages - FAST version.
    Returns a comprehensive description for keyword filtering and blog generation.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    # Just fetch homepage and maybe one other page - much faster
    key_pages = []

    for url_data in urls:
        slug = url_data.get('slug', '').lower().rstrip('/')
        if slug == '' or slug == '/':
            key_pages.insert(0, url_data)
        elif '/about' in slug or '/product' in slug or '/feature' in slug:
            if len(key_pages) < 2:
                key_pages.append(url_data)

    if not key_pages and urls:
        key_pages = [urls[0]]

    page_contents = []

    # Fetch just 2 pages max for speed
    for url_data in key_pages[:2]:
        try:
            resp = session.get(url_data['url'], timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'footer']):
                    tag.decompose()

                meta = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta.get('content', '') if meta else ''

                text = soup.get_text(' ', strip=True)[:1500]
                page_contents.append(f"Meta: {meta_desc}\nContent: {text[:800]}")
        except:
            continue

    if not page_contents:
        return f"{company_name} is a software company."

    combined_content = "\n---\n".join(page_contents)

    prompt = f"""From this website content, describe what {company_name} does in 2 sentences:

{combined_content}

Return ONLY a 2-sentence description of the product/company."""

    try:
        response = api_client.call(prompt, model="haiku", max_tokens=150)
        return response.strip()
    except:
        return f"{company_name} is a software company."


def learn_blog_structure(api_client, urls, company_name):
    """Learn comprehensive blog and webpage style from existing pages"""
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    # Collect blog pages
    blog_urls = [u for u in urls if '/blog/' in u['url'] or '/post/' in u['url'] or '/article/' in u['url']][:10]

    # Also collect some regular pages for overall brand voice
    other_urls = [u for u in urls if '/blog/' not in u['url'] and '/post/' not in u['url']][:5]

    all_page_data = []

    # Fetch and analyze blog pages in detail
    for url_data in blog_urls:
        try:
            resp = session.get(url_data['url'], timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Extract structured data
                page_data = {
                    'url': url_data['url'],
                    'type': 'blog',
                    'title': '',
                    'headings': [],
                    'content': '',
                    'lists': 0,
                    'images': 0,
                    'links': 0
                }

                # Get title
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    page_data['title'] = title_tag.get_text(strip=True)

                # Get all headings structure
                for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                    page_data['headings'].append({
                        'level': h.name,
                        'text': h.get_text(strip=True)[:100]
                    })

                # Count structural elements
                page_data['lists'] = len(soup.find_all(['ul', 'ol']))
                page_data['images'] = len(soup.find_all('img'))
                page_data['links'] = len(soup.find_all('a'))

                # Get main content
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    tag.decompose()
                page_data['content'] = soup.get_text(' ', strip=True)[:3000]

                all_page_data.append(page_data)
        except:
            continue

    # Fetch regular pages for brand voice
    for url_data in other_urls:
        try:
            resp = session.get(url_data['url'], timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                text = soup.get_text(' ', strip=True)[:1500]
                all_page_data.append({
                    'url': url_data['url'],
                    'type': 'page',
                    'content': text
                })
        except:
            continue

    if not all_page_data:
        return default_style()

    # Build comprehensive analysis prompt
    blog_samples = [p for p in all_page_data if p.get('type') == 'blog'][:3]
    page_samples = [p for p in all_page_data if p.get('type') == 'page'][:2]

    analysis_text = f"BLOG PAGES FROM {company_name}:\n\n"
    for i, blog in enumerate(blog_samples, 1):
        analysis_text += f"Blog {i}: {blog.get('title', 'Untitled')}\n"
        analysis_text += f"Headings: {json.dumps(blog.get('headings', [])[:8])}\n"
        analysis_text += f"Lists: {blog.get('lists', 0)}, Images: {blog.get('images', 0)}\n"
        analysis_text += f"Content excerpt: {blog.get('content', '')[:1000]}\n\n"

    if page_samples:
        analysis_text += "OTHER PAGES (brand voice):\n"
        for page in page_samples:
            analysis_text += f"{page.get('content', '')[:500]}\n\n"

    prompt = f"""Analyze {company_name}'s writing style in comprehensive detail:

{analysis_text}

Extract a detailed style guide with:

1. TONE: Overall voice (formal/casual/professional/friendly), personality traits
2. VOCABULARY: Common terms, industry jargon they use, words to avoid
3. SENTENCE STRUCTURE: Short/long sentences, complexity level, use of questions
4. PARAGRAPH STYLE: Length, how they start paragraphs, transitions
5. HEADER PATTERNS: H2/H3 naming style, question vs statement headers
6. LIST USAGE: Bullet vs numbered, frequency, what they list
7. CTA STYLE: How they encourage action, button text patterns
8. UNIQUE PHRASES: Brand-specific phrases, taglines, repeated expressions
9. FORMATTING: Use of bold, italics, callouts, quotes
10. CONTENT STRUCTURE: How they open articles, middle section patterns, conclusions

Return detailed JSON:
{{
  "tone": "detailed description of voice and personality",
  "vocabulary": {{"use": ["terms they use"], "avoid": ["terms to avoid"]}},
  "sentences": "description of sentence style",
  "paragraphs": "paragraph structure description",
  "headers": "header naming patterns and style",
  "lists": "how and when they use lists",
  "cta": "call-to-action style description",
  "phrases": ["unique phrases", "brand expressions"],
  "formatting": "bold, italic, callout usage",
  "structure": "article structure pattern"
}}"""

    try:
        response = api_client.call(prompt, model="sonnet", max_tokens=1500)
        # Find JSON in response
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            style = json.loads(match.group())
            # Ensure all expected keys exist
            default = default_style()
            for key in default:
                if key not in style:
                    style[key] = default[key]
            return style
    except Exception as e:
        pass

    return default_style()


def default_style():
    return {
        "tone": "professional but friendly, approachable and helpful",
        "vocabulary": {"use": [], "avoid": ["leverage", "synergy", "utilize"]},
        "sentences": "mix of short and medium length, varied structure",
        "paragraphs": "medium length, 3-5 sentences, clear topic sentences",
        "headers": "clear H2 sections with H3 subsections, statement style",
        "lists": "moderate use for key points and steps",
        "cta": "soft CTAs woven into content naturally",
        "phrases": [],
        "formatting": "occasional bold for emphasis, minimal italics",
        "structure": "hook intro, problem-solution body, actionable conclusion"
    }


def build_link_map(urls):
    """Build keyword to URL mapping for internal links"""
    link_map = {}
    
    for url_data in urls:
        # Only English URLs
        if is_non_english_url(url_data['url']):
            continue
        
        slug = url_data.get('slug', '').lower().strip('/')
        if not slug:
            continue
        
        parts = slug.split('/')
        for part in parts:
            words = re.split(r'[-_]', part)
            words = [w for w in words if len(w) >= 4]
            
            if len(words) >= 2:
                keyword = ' '.join(words)
                # Prefer English base URLs
                if keyword not in link_map:
                    link_map[keyword] = url_data['url']
    
    return link_map


def generate_blog(api_client, keyword, kw_type, company_name, company_style, link_map, competitors, company_description="", blog_angle="", content_type="auto", custom_structure="", include_faqs=True, qa_format=False):
    """Generate high-quality SEO blog tailored for the company and content type"""

    current_year = datetime.now().year

    # Get relevant internal links
    links_text = ""
    kw_words = set(keyword.lower().split())
    relevant_links = []
    for link_kw, url in link_map.items():
        if any(w in link_kw for w in kw_words):
            relevant_links.append(f"- [{link_kw}]({url})")
    links_text = '\n'.join(relevant_links[:5]) if relevant_links else "None available"

    style_info = json.dumps(company_style, indent=2) if company_style else "Professional, friendly tone"

    # Determine content type if auto
    if content_type == 'auto':
        kw_lower = kw_type.lower() if kw_type else ''
        if 'comparison' in kw_lower or 'vs' in keyword.lower():
            content_type = 'comparison'
        elif 'alternative' in kw_lower:
            content_type = 'alternative'
        elif 'how-to' in kw_lower or 'how to' in keyword.lower():
            content_type = 'how_to'
        elif 'listicle' in kw_lower or 'top' in keyword.lower() or 'best' in keyword.lower():
            content_type = 'listicle'
        elif 'tool' in kw_lower:
            content_type = 'tool_page'
        elif 'solution' in kw_lower:
            content_type = 'solution_page'
        else:
            content_type = 'blog'

    # Get structure template
    if custom_structure:
        structure_template = custom_structure
    elif content_type in CONTENT_TYPES:
        structure_template = CONTENT_TYPES[content_type]['structure']
    else:
        structure_template = CONTENT_TYPES['blog']['structure']

    # Determine content angle based on content type
    content_angle = blog_angle
    if not content_angle:
        if content_type == 'comparison':
            content_angle = f"Compare the tools objectively but highlight where {company_name} excels. Include {company_name} in the comparison table."
        elif content_type == 'alternative':
            content_angle = f"Position {company_name} as a strong alternative. Explain why someone might choose {company_name} over the main product."
        elif content_type == 'how_to':
            content_angle = f"Show how to accomplish this task, with specific examples using {company_name}. Include step-by-step instructions."
        elif content_type == 'listicle':
            content_angle = f"Create a comprehensive list. Naturally include {company_name} where relevant with honest positioning."
        elif content_type == 'tool_page':
            content_angle = f"Create a compelling product page showcasing {company_name}'s features and benefits for this use case."
        elif content_type == 'solution_page':
            content_angle = f"Address the pain point directly and position {company_name} as the solution with clear benefits."
        else:
            content_angle = f"Write informative content that demonstrates {company_name}'s expertise in this area."

    prompt = f"""You are a senior SEO content writer for {company_name}. Write a comprehensive, high-quality {CONTENT_TYPES.get(content_type, {}).get('name', 'blog post')}.

ABOUT {company_name.upper()}:
{company_description}

TARGET KEYWORD: {keyword}
CONTENT TYPE: {CONTENT_TYPES.get(content_type, {}).get('name', 'Blog Post')}
CURRENT YEAR: {current_year}
COMPETITORS COVERING THIS: {competitors}

CONTENT ANGLE:
{content_angle}

COMPANY WRITING STYLE:
{style_info}

INTERNAL LINKS TO INCLUDE (use naturally):
{links_text}

CRITICAL REQUIREMENTS:

1. LENGTH: Minimum 2500 words. Make every section substantial.

2. {company_name.upper()} INTEGRATION:
   - Naturally weave in {company_name}'s capabilities where relevant
   - For comparisons: include {company_name} as a strong contender
   - For alternatives: position {company_name} as a compelling option
   - For how-tos: show how {company_name} makes this easier
   - Don't be overly promotional; be helpful and honest
   - Mention specific {company_name} features that relate to the topic

3. SEO OPTIMIZATION:
   - Include keyword in title, first paragraph, and 2-3 H2 headers
   - Use related keywords naturally throughout
   - Meta title: 50-60 characters (concise, keyword-focused)
   - Meta description: 150-160 characters (compelling, includes keyword)

4. FOLLOW THIS STRUCTURE TEMPLATE:
{structure_template}

5. WRITING RULES:
   - NO dashes (—, –) for separating clauses. Use commas or periods.
   - NO AI phrases: "in today's world", "let's dive in", "it's worth noting", "leverage", "utilize"
   - USE contractions naturally (don't, can't, it's, you'll)
   - VARY sentence length
   - INCLUDE specific numbers, statistics, examples
   - USE "you" and "your" to address reader directly

6. INTERNAL LINKS:
   - Add 3-5 internal links to {company_name} pages
   - Use natural anchor text
   - Only use links from the list provided above
   - Links should be to ENGLISH pages only

7. DATES:
   - Use {current_year} for all current references
   - Never use 2024, 2023, or older as "current"

{"8. Q&A FORMAT: Structure the entire content as questions and answers. Each H2 heading should be a question that readers commonly ask. The content under each H2 should directly answer that question. This makes the content scannable and directly addresses user intent." if qa_format else ""}

{"9. FAQs SECTION: At the END of the article, include a section titled '## Frequently Asked Questions' with 4-5 relevant FAQs. Format each FAQ as: '### Q: [Question]' followed by 'A: [Answer]'. Make questions specific to the topic and answers concise but helpful (2-3 sentences each)." if include_faqs else ""}

OUTPUT FORMAT:
TITLE: [Your title]
META: [150-160 char description]
CONTENT:
[Full markdown content, 2500+ words{", ending with FAQs section" if include_faqs else ""}]"""

    response = api_client.call(prompt, model="sonnet", max_tokens=6000)
    
    # Parse response
    result = {
        'title': f"{keyword} Guide {current_year}",
        'meta_description': f"Learn about {keyword}.",
        'content': response,
        'word_count': 0
    }
    
    # Extract title
    title_match = re.search(r'TITLE:\s*(.+?)(?:\n|META)', response, re.I)
    if title_match:
        result['title'] = title_match.group(1).strip()
    
    # Extract meta
    meta_match = re.search(r'META:\s*(.+?)(?:\n|CONTENT)', response, re.I)
    if meta_match:
        result['meta_description'] = meta_match.group(1).strip()[:160]
    
    # Extract content
    content_match = re.search(r'CONTENT:\s*(.+)', response, re.I | re.DOTALL)
    if content_match:
        result['content'] = content_match.group(1).strip()
    
    # Clean content
    content = result['content']
    content = re.sub(r'\s*[—–]\s*', ', ', content)  # Remove dashes
    content = re.sub(r'\s+-\s+', ', ', content)
    
    # Update old years
    for year in ['2024', '2023', '2022']:
        content = re.sub(rf'\b{year}\b', str(current_year), content)
    
    result['content'] = content
    result['word_count'] = len(content.split())
    
    return result


def export_to_notion_format(blogs):
    """Create ZIP file with individual markdown files for Notion import"""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, blog in enumerate(blogs, 1):
            title = blog.get('title', f'Blog {i}')
            keyword = blog.get('keyword', '')
            meta_desc = blog.get('meta_description', '')
            content = blog.get('content', '')

            # Create markdown content with frontmatter for Notion
            md_content = f"""# {title}

**Keyword:** {keyword}
**Meta Description:** {meta_desc}

---

{content}
"""
            # Create safe filename from title
            safe_title = re.sub(r'[^\w\s-]', '', title)[:50].strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{i:02d}_{safe_title}.md"

            zip_file.writestr(filename, md_content)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def generate_cover_image(title: str, template_path: str = None) -> bytes:
    """Generate cover image with blog title - works on cloud deployment"""
    img_width, img_height = 1200, 630
    use_template = False

    # Try to load template image from repo
    template_paths = [
        Path(__file__).parent / "template.png",  # Same folder as app
        Path("template.png"),  # Current directory
        Path("/mount/src/trublog-writer/template.png"),  # Streamlit Cloud path
    ]

    img = None
    for tp in template_paths:
        if tp.exists():
            try:
                img = Image.open(tp).convert('RGB')
                img_width, img_height = img.size
                use_template = True
                break
            except:
                pass

    # Define text box area (used for both template and fallback)
    margin = 80
    rect_y1 = margin + 20  # Moved higher
    rect_y2 = img_height - margin - 80

    # Fallback: Create gradient background
    if img is None:
        img = Image.new('RGB', (img_width, img_height), (99, 102, 241))

        # Add gradient effect
        draw = ImageDraw.Draw(img)
        for y in range(img_height):
            r = int(99 + (139 - 99) * y / img_height)
            g = int(102 + (92 - 102) * y / img_height)
            b = int(241 + (246 - 241) * y / img_height)
            draw.line([(0, y), (img_width, y)], fill=(r, g, b))

        # Draw white rounded rectangle in center for text
        rect_x1 = margin
        rect_x2 = img_width - margin

        draw.rounded_rectangle(
            [(rect_x1, rect_y1), (rect_x2, rect_y2)],
            radius=20,
            fill=(255, 255, 255)
        )
    else:
        draw = ImageDraw.Draw(img)

    # Load font - try Inter Bold first (bundled with app), then system fonts
    font_size = 45
    font = None
    try:
        # Inter Bold bundled with app (works on all platforms)
        script_dir = Path(__file__).parent
        inter_bold = script_dir / "Inter-Bold.ttf"

        # Fallback fonts
        fallback_fonts = [
            # Linux fonts (Streamlit Cloud)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            # Mac fonts
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]

        # Try Inter Bold first
        if inter_bold.exists():
            font = ImageFont.truetype(str(inter_bold), font_size)
        else:
            for fp in fallback_fonts:
                if Path(fp).exists():
                    font = ImageFont.truetype(fp, font_size)
                    break
    except:
        pass

    if font is None:
        # Use default font with larger size simulation
        font = ImageFont.load_default()

    # Wrap text to fit in the box
    max_chars_per_line = 30
    wrapped_lines = textwrap.wrap(title, width=max_chars_per_line)

    # Limit to 3 lines max
    if len(wrapped_lines) > 3:
        wrapped_lines = wrapped_lines[:3]
        if len(wrapped_lines[2]) > max_chars_per_line - 3:
            wrapped_lines[2] = wrapped_lines[2][:max_chars_per_line-3] + "..."

    # Calculate text positioning
    line_height = font_size + 15
    total_text_height = len(wrapped_lines) * line_height

    # Center text in white box
    box_center_y = (rect_y1 + rect_y2) // 2
    current_y = box_center_y - total_text_height // 2

    # Text color: #707be5 (Trupeer purple)
    text_color = (112, 123, 229)  # #707be5

    for line in wrapped_lines:
        # Get text bounding box for centering
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(line) * 20  # Fallback width estimate

        x = (img_width - text_width) // 2
        draw.text((x, current_y), line, font=font, fill=text_color)
        current_y += line_height

    # Save to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer.getvalue()


def infer_category(blog: dict) -> str:
    """Infer category from blog type and content"""
    blog_type = blog.get('type', '').lower()
    title = blog.get('title', '').lower()
    keyword = blog.get('keyword', '').lower()

    # Map common blog types to categories
    type_to_category = {
        'comparison': 'Comparison',
        'alternative': 'Alternative',
        'alternatives': 'Alternative',
        'vs': 'Comparison',
        'how to': 'Instructional Videos',
        'how-to': 'Instructional Videos',
        'tutorial': 'Product Demos',
        'guide': 'Instructional Design',
        'best': 'Comparison',
        'top': 'Comparison',
        'review': 'Product Updates',
        'what is': 'Instructional Design',
    }

    # Check blog type first
    for key, category in type_to_category.items():
        if key in blog_type:
            return category

    # Check title and keyword for category hints
    content_hints = {
        'onboarding': 'Customer Onboarding',
        'training': 'Training Videos',
        'sales': 'Sales Videos',
        'sop': 'SOP',
        'standard operating': 'SOP',
        'demo': 'Product Demos',
        'update': 'Product Updates',
        'new feature': 'Product Updates',
        'alternative': 'Alternative',
        'vs': 'Comparison',
        'versus': 'Comparison',
        'compare': 'Comparison',
        'how to': 'Instructional Videos',
        'step by step': 'SOP Creation Software',
        'create': 'Instructional Design',
    }

    combined_text = f"{title} {keyword}"
    for hint, category in content_hints.items():
        if hint in combined_text:
            return category

    # Default category
    return 'Instructional Design'


def create_slug(title: str, keyword: str = None) -> str:
    """Create URL-friendly slug from keyword/title - SEO optimized, short"""
    # Prefer keyword for slug (more SEO friendly)
    text = keyword if keyword else title

    # Remove common filler words for shorter slug
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                  'how', 'what', 'why', 'when', 'where', 'is', 'are', 'was', 'were', 'your', 'you',
                  'complete', 'guide', 'ultimate', 'best', 'top']

    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    words = slug.split()

    # Remove stop words but keep important keywords
    clean_words = [w for w in words if w not in stop_words or len(words) <= 3]

    # If too many words removed, use first few original words
    if len(clean_words) < 2:
        clean_words = words[:4]

    slug = '-'.join(clean_words[:5])  # Max 5 words for short slug
    slug = re.sub(r'-+', '-', slug).strip('-')

    return slug[:50]  # Limit to 50 chars for short, clean slug


def create_meta_title(title: str, keyword: str = None) -> str:
    """Create SEO meta title - 50-60 characters"""
    # Start with title, trim to fit
    meta = title

    # If too long, try to shorten intelligently
    if len(meta) > 60:
        # Try removing year if present
        meta = re.sub(r'\s*\(\d{4}\)\s*', '', meta)
        meta = re.sub(r'\s*\d{4}\s*', '', meta)

    # Still too long? Truncate at word boundary
    if len(meta) > 60:
        words = meta.split()
        meta = ''
        for word in words:
            if len(meta + ' ' + word) <= 57:
                meta = (meta + ' ' + word).strip()
            else:
                break
        meta = meta + '...' if meta != title else meta

    # Too short? Add keyword
    if len(meta) < 50 and keyword and keyword.lower() not in meta.lower():
        meta = f"{meta} | {keyword}"[:60]

    return meta[:60]


def create_meta_description(description: str, keyword: str = None) -> str:
    """Create SEO meta description - 150-160 characters"""
    meta = description

    # If too short, pad with keyword info
    if len(meta) < 150 and keyword:
        meta = f"{meta} Learn about {keyword}."

    # If too long, truncate at sentence or word boundary
    if len(meta) > 160:
        # Try to cut at sentence
        sentences = re.split(r'[.!?]', meta)
        meta = ''
        for sent in sentences:
            if len(meta + sent + '.') <= 157:
                meta = meta + sent.strip() + '. '
            else:
                break
        meta = meta.strip()

        # Still too long? Cut at word
        if len(meta) > 160 or len(meta) < 100:
            words = description.split()
            meta = ''
            for word in words:
                if len(meta + ' ' + word) <= 157:
                    meta = (meta + ' ' + word).strip()
                else:
                    break
            meta = meta + '...'

    return meta[:160]


def export_to_framer_format(blogs: list, template_path: str = None) -> bytes:
    """Create ZIP with CSV and cover images for Framer CMS import"""
    zip_buffer = io.BytesIO()

    csv_data = []
    current_date = datetime.now().strftime('%Y-%m-%d')

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, blog in enumerate(blogs, 1):
            title = blog.get('title', f'Blog {i}')
            keyword = blog.get('keyword', '')
            slug = create_slug(title, keyword)

            # Generate cover image
            image_bytes = generate_cover_image(title, template_path)
            image_filename = f"images/{slug}.png"
            zip_file.writestr(image_filename, image_bytes)

            # Prepare CSV row with Framer CMS fields - SEO optimized
            meta_title = create_meta_title(title, keyword)
            meta_desc = create_meta_description(blog.get('meta_description', ''), keyword)

            csv_data.append({
                'Title': title,
                'Slug': slug,
                'Published Date': current_date,
                'Image': image_filename,
                'Category': infer_category(blog),
                'MetaTitle': meta_title,  # 50-60 chars
                'MetaDescription': meta_desc,  # 150-160 chars
                'Content': blog.get('content', '')
            })

        # Create CSV file
        df = pd.DataFrame(csv_data)
        csv_content = df.to_csv(index=False)
        zip_file.writestr('framer_blogs.csv', csv_content)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# ============================================
# MAIN APP
# ============================================

def main():
    # Header
    st.markdown("<h1 style='font-size: 5rem; margin-bottom: 0; font-weight: 700;'>TruBlog Writer</h1>", unsafe_allow_html=True)
    st.caption("Find Keywords and Generate Blogs")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Scoring")
        st.caption("Priority = Total keyword occurrences across competitor URLs")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Setup & Analyze",
        "2️⃣ Keyword Gaps",
        "3️⃣ Generate Blogs",
        "4️⃣ Export"
    ])
    
    # ============================================
    # TAB 1: SETUP
    # ============================================
    with tab1:
        st.subheader("Your Company")
        
        col1, col2 = st.columns([2, 1])

        with col1:
            company_name = st.text_input(
                "Company Name",
                value=st.session_state.my_company_name,
                placeholder="e.g., Trupeer"
            )

            company_domain = st.text_input(
                "Company Domain (required)",
                value=st.session_state.my_company_domain,
                placeholder="e.g., trupeer.ai",
                help="Enter your exact website domain without https:// or www."
            )

            st.caption("Please verify this is your correct domain before proceeding.")

        st.subheader("Competitors")

        competitors = st.text_area(
            "Competitor Names (one per line)",
            value=st.session_state.competitor_names,
            placeholder="Synthesia\nLoom\nScribe\nGuidde\nVidyard",
            height=150
        )

        col_analyze, col_quick = st.columns(2)

        # Start Analysis Button
        with col_analyze:
            analyze_clicked = st.button("🚀 Full Analysis", type="primary", use_container_width=True)

        # Quick Start Button - Skip analysis, go directly to custom keywords
        with col_quick:
            quick_start = st.button("⚡ Quick Start (Custom Keywords)", use_container_width=True)

        if quick_start:
            if not company_name:
                st.error("Please enter your company name")
            elif not company_domain:
                st.error("Please enter your company domain")
            else:
                # Save inputs
                st.session_state.my_company_name = company_name
                domain = company_domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
                st.session_state.my_company_domain = domain

                # Quick learn company context
                api_client = APIClient(st.session_state.api_key)
                st.session_state.company_description = f"{company_name} is a video creation and screen recording platform for tutorials, demos, and training content."

                # Set minimal defaults
                st.session_state.my_urls = []
                st.session_state.my_keywords = set()
                st.session_state.competitor_data = {}
                st.session_state.company_style = default_style()
                st.session_state.link_map = {}
                st.session_state.gap_keywords = []
                st.session_state.selected_keywords = []
                st.session_state.analysis_done = True

                st.success("✅ Quick Start ready! Go to Tab 2 to add custom keywords, then generate blogs.")
                st.info("💡 Tip: Add your keywords in Tab 2 using 'Add Custom Keywords' section")

        if analyze_clicked:
            if not company_name:
                st.error("Please enter your company name")
                return
            
            if not competitors:
                st.error("Please enter at least one competitor")
                return

            if not company_domain:
                st.error("Please enter your company domain")
                return

            api_client = APIClient(st.session_state.api_key)

            # Save inputs
            st.session_state.my_company_name = company_name
            st.session_state.competitor_names = competitors

            # Clean domain input
            domain = company_domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            st.session_state.my_company_domain = domain

            progress = st.progress(0)
            status = st.empty()

            st.write(f"✅ Using domain: **{domain}**")

            progress.progress(10)
            
            # Step 2: Fetch my sitemap
            status.text(f"📥 Fetching {domain} sitemap...")
            my_urls = fetch_sitemap(domain)
            st.session_state.my_urls = my_urls
            st.write(f"✅ Found **{len(my_urls)}** pages on your site")
            
            progress.progress(25)

            # Step 3: Extract my keywords using content-based approach
            status.text("🔑 Extracting your keywords from page content...")
            my_keywords_data = extract_keywords_from_urls(my_urls, max_pages=40)
            my_keywords = set()
            for kw_data in my_keywords_data:
                kw_lower = kw_data['keyword'].lower().strip()
                if len(kw_lower) >= 10:  # Skip short/generic
                    my_keywords.add(kw_lower)
            st.session_state.my_keywords = my_keywords
            st.write(f"✅ Found **{len(my_keywords)}** keywords on your site")
            
            progress.progress(35)
            
            # Step 4: Learn style
            status.text("📖 Learning your writing style...")
            style = learn_blog_structure(api_client, my_urls, company_name)
            st.session_state.company_style = style
            
            progress.progress(40)
            
            # Step 5: Build link map
            status.text("🔗 Building internal link map...")
            link_map = build_link_map(my_urls)
            st.session_state.link_map = link_map
            st.write(f"✅ Found **{len(link_map)}** internal link opportunities")
            
            progress.progress(45)
            
            # Step 6: Fetch competitor sitemaps
            comp_list = [c.strip() for c in competitors.split('\n') if c.strip()]
            
            # Find competitor domains
            status.text("🔍 Finding competitor domains...")
            comp_domains = {}
            for comp in comp_list:
                domain = find_domain_from_name(api_client, comp)
                comp_domains[comp] = domain
                st.write(f"  • {comp}: **{domain}**")
            
            progress.progress(55)
            
            # Fetch competitor sitemaps
            competitor_data = {}
            for i, (comp_name, comp_domain) in enumerate(comp_domains.items()):
                status.text(f"📥 Fetching {comp_name} sitemap...")
                urls = fetch_sitemap(comp_domain)
                competitor_data[comp_name] = {'domain': comp_domain, 'urls': urls}
                st.write(f"  • {comp_name}: **{len(urls)}** pages")
                progress.progress(55 + (i + 1) * 25 // len(comp_domains))
            
            st.session_state.competitor_data = competitor_data
            
            progress.progress(80)

            # Step 7: Extract keywords directly from competitor URLs (simple sitemap comparison)
            status.text("🔑 Extracting keywords from competitor pages...")
            all_keywords = defaultdict(lambda: {
                'frequency': 0,
                'competitors': set(),
                'type': 'Blog',
                'urls': []
            })

            total_comps = len(competitor_data)
            for comp_idx, (comp_name, data) in enumerate(competitor_data.items()):
                status.text(f"🔑 Analyzing {comp_name} pages ({comp_idx + 1}/{total_comps})...")

                # Extract keywords from ALL URLs (not just 40)
                comp_keywords = extract_keywords_from_urls(data['urls'], max_pages=500)

                st.write(f"  • {comp_name}: **{len(comp_keywords)}** keywords from {len(data['urls'])} pages")

                for kw_data in comp_keywords:
                    kw_lower = kw_data['keyword'].lower().strip()

                    # Skip very short keywords
                    if len(kw_lower) < 8:
                        continue

                    all_keywords[kw_lower]['frequency'] += 1
                    all_keywords[kw_lower]['competitors'].add(comp_name)
                    all_keywords[kw_lower]['type'] = kw_data['type']
                    if len(all_keywords[kw_lower]['urls']) < 5:
                        all_keywords[kw_lower]['urls'].append(kw_data.get('url', ''))

            st.session_state.all_keywords = dict(all_keywords)
            st.write(f"✅ Total unique keywords from competitors: **{len(all_keywords)}**")

            progress.progress(85)

            # Step 8: Learn about company
            status.text(f"🧠 Learning about {company_name}...")
            company_description = f"{company_name} is a video creation and screen recording platform for tutorials, demos, and training content."
            st.session_state.company_description = company_description

            progress.progress(90)

            # Step 9: Direct gap analysis - compare with Trupeer's keywords
            status.text("📊 Finding keyword gaps (what competitors have that you don't)...")
            gap_keywords = []

            # Get Trupeer's keywords (lowercase for comparison)
            my_kw_lower = {kw.lower() for kw in st.session_state.my_keywords}

            for kw, data in all_keywords.items():
                kw_lower = kw.lower()

                # Check if Trupeer has similar content
                has_it = False
                for my_kw in my_kw_lower:
                    # Check for significant overlap
                    kw_words = set(kw_lower.split())
                    my_words = set(my_kw.split())
                    overlap = len(kw_words & my_words)
                    if overlap >= 2 or kw_lower in my_kw or my_kw in kw_lower:
                        has_it = True
                        break

                # Priority = number of competitors covering this topic
                priority = data['frequency'] * len(data['competitors'])

                gap_keywords.append({
                    'keyword': kw.title(),
                    'type': data['type'],
                    'occurrences': data['frequency'],
                    'competitors': ', '.join(sorted(data['competitors'])),
                    'priority': priority,
                    'you_have': 'Yes' if has_it else 'No',
                    'urls': data['urls']
                })
            
            # Deduplicate keywords by keyword name (keep highest priority)
            seen_keywords = {}
            for kw in gap_keywords:
                kw_lower = kw['keyword'].lower()
                if kw_lower not in seen_keywords or kw['priority'] > seen_keywords[kw_lower]['priority']:
                    seen_keywords[kw_lower] = kw
            gap_keywords = list(seen_keywords.values())

            # Sort: Gaps first (you don't have), then by priority (occurrences)
            gap_keywords.sort(key=lambda x: (x['you_have'] == 'Yes', -x['priority']))

            st.session_state.gap_keywords = gap_keywords
            st.session_state.analysis_done = True

            progress.progress(100)
            status.text("✅ Analysis complete!")

            # Summary metrics
            gaps_count = len([k for k in gap_keywords if k['you_have'] == 'No'])
            st.markdown(f"""
            <div class="success-box">
                <strong>🎉 Analysis Complete!</strong><br>
                Found <strong>{gaps_count} keyword gaps</strong> out of {len(gap_keywords)} total keywords.
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================
    # TAB 2: KEYWORD GAPS
    # ============================================
    with tab2:
        if not st.session_state.analysis_done:
            st.warning("⚠️ Please complete the analysis in Tab 1 first, or use Quick Start to add custom keywords directly.")

            # Still show Add Custom Keywords for Quick Start users
            st.markdown("---")
            st.markdown("### ➕ Add Custom Keywords")
            st.caption("Add your own keywords to generate content for")

            custom_keywords_early = st.text_area(
                "Enter keywords (one per line)",
                placeholder="AI video generator\nScreen recording tool\nLoom alternative\nHow to create product demos",
                height=150,
                key="custom_kw_early"
            )

            if st.button("➕ Add Keywords", type="primary", key="add_kw_early"):
                if custom_keywords_early:
                    added = 0
                    for kw in custom_keywords_early.split('\n'):
                        kw = kw.strip()
                        if kw and len(kw) > 3:
                            # Detect type from keyword
                            kw_lower = kw.lower()
                            if 'vs' in kw_lower or 'versus' in kw_lower:
                                kw_type = 'Comparison'
                            elif 'alternative' in kw_lower:
                                kw_type = 'Alternative'
                            elif 'how to' in kw_lower or 'tutorial' in kw_lower:
                                kw_type = 'How-To'
                            elif 'best' in kw_lower or 'top' in kw_lower:
                                kw_type = 'Listicle'
                            else:
                                kw_type = 'Blog'

                            st.session_state.selected_keywords.append({
                                'keyword': kw,
                                'type': kw_type,
                                'frequency': 0,
                                'competitors': 'Custom',
                                'priority': 100,
                                'you_have': 'No'
                            })
                            added += 1
                    if added > 0:
                        st.success(f"✅ Added {added} keywords! Go to Tab 3 to generate content.")
                        st.rerun()

            # Show selected keywords before return
            if st.session_state.selected_keywords:
                st.markdown("---")
                st.markdown(f"### ✅ {len(st.session_state.selected_keywords)} Keywords Ready")
                for kw in st.session_state.selected_keywords:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• **{kw['keyword']}** ({kw['type']})")
                    with col2:
                        if st.button("🗑️", key=f"del_early_{kw['keyword'][:20]}"):
                            st.session_state.selected_keywords.remove(kw)
                            st.rerun()
                st.info("👉 Go to **Tab 3** to generate content for these keywords")

        # Always show Add Custom Keywords section (for both Quick Start and Full Analysis)
        st.markdown("### ➕ Add Custom Keywords")
        col_input, col_btn = st.columns([3, 1])

        with col_input:
            custom_keywords_input = st.text_input(
                "Add keyword",
                placeholder="e.g., best screen recording software, loom vs vidyard",
                key="custom_kw_input",
                label_visibility="collapsed"
            )

        with col_btn:
            if st.button("➕ Add", type="primary", key="add_single_kw"):
                if custom_keywords_input and len(custom_keywords_input.strip()) > 3:
                    kw = custom_keywords_input.strip()
                    kw_lower = kw.lower()

                    # Detect type
                    if 'vs' in kw_lower or 'versus' in kw_lower:
                        kw_type = 'Comparison'
                    elif 'alternative' in kw_lower:
                        kw_type = 'Alternative'
                    elif 'how to' in kw_lower:
                        kw_type = 'How-To'
                    elif 'best' in kw_lower or 'top' in kw_lower:
                        kw_type = 'Listicle'
                    else:
                        kw_type = 'Blog'

                    st.session_state.selected_keywords.append({
                        'keyword': kw,
                        'type': kw_type,
                        'frequency': 0,
                        'competitors': 'Custom',
                        'priority': 100,
                        'you_have': 'No'
                    })
                    st.success(f"✅ Added: {kw}")
                    st.rerun()

        # Bulk add option
        with st.expander("📝 Bulk add multiple keywords"):
            bulk_keywords = st.text_area(
                "Enter keywords (one per line)",
                placeholder="AI video generator\nScreen recording tool\nLoom alternative\nHow to create product demos",
                height=120,
                key="bulk_kw"
            )
            if st.button("Add All Keywords", key="add_bulk"):
                if bulk_keywords:
                    added = 0
                    for kw in bulk_keywords.split('\n'):
                        kw = kw.strip()
                        if kw and len(kw) > 3:
                            kw_lower = kw.lower()
                            if 'vs' in kw_lower:
                                kw_type = 'Comparison'
                            elif 'alternative' in kw_lower:
                                kw_type = 'Alternative'
                            elif 'how to' in kw_lower:
                                kw_type = 'How-To'
                            elif 'best' in kw_lower or 'top' in kw_lower:
                                kw_type = 'Listicle'
                            else:
                                kw_type = 'Blog'

                            st.session_state.selected_keywords.append({
                                'keyword': kw,
                                'type': kw_type,
                                'frequency': 0,
                                'competitors': 'Custom',
                                'priority': 100,
                                'you_have': 'No'
                            })
                            added += 1
                    if added > 0:
                        st.success(f"✅ Added {added} keywords!")
                        st.rerun()

        # Show currently selected keywords
        if st.session_state.selected_keywords:
            st.markdown(f"**{len(st.session_state.selected_keywords)} keywords selected for content generation**")
            with st.expander("View selected keywords"):
                for i, kw in enumerate(st.session_state.selected_keywords):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• **{kw['keyword']}** ({kw['type']})")
                    with col2:
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state.selected_keywords.pop(i)
                            st.rerun()

            if st.button("🗑️ Clear All Selected", key="clear_selected"):
                st.session_state.selected_keywords = []
                st.rerun()

        # Gap Analysis Section - only show if analysis was done
        if st.session_state.analysis_done and st.session_state.gap_keywords:
            st.markdown("---")
            st.subheader("📊 Keyword Gap Analysis")

            gap_keywords = st.session_state.gap_keywords

            # Simple metrics
            total_kw = len(gap_keywords)
            gaps = [k for k in gap_keywords if k['you_have'] == 'No']
            has_kw = [k for k in gap_keywords if k['you_have'] == 'Yes']

            col1, col2, col3 = st.columns(3)
            col1.metric("Gaps (Missing)", len(gaps))
            col2.metric("Already Have", len(has_kw))
            col3.metric("Total Keywords", total_kw)

            st.caption("**Priority Score** = Total occurrences across competitor URLs. Higher = more competitors targeting this keyword.")

            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                show_only_gaps = st.checkbox("Show only gaps", value=True)
            with col2:
                min_occurrences = st.slider("Minimum occurrences", 1, 20, 1)

            # Filter keywords
            filtered = gap_keywords
            if show_only_gaps:
                filtered = [k for k in filtered if k['you_have'] == 'No']
            filtered = [k for k in filtered if k.get('priority', 0) >= min_occurrences]

            st.write(f"Showing **{len(filtered)}** keywords")

            # Create DataFrame for display
            df = pd.DataFrame(filtered) if filtered else pd.DataFrame()

            if len(df) > 0:
                # Add selection column
                df.insert(0, 'Select', False)

                # Reorder and select columns
                columns = ['Select', 'keyword', 'type', 'priority', 'competitors', 'you_have']
                df = df[[c for c in columns if c in df.columns]]

                # Rename columns for display
                df.columns = ['Select', 'Keyword', 'Type', 'Occurrences', 'Competitors', 'You Have?']

                # Simple table display
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("", default=False),
                        "Occurrences": st.column_config.NumberColumn("Occurrences"),
                        "Keyword": st.column_config.TextColumn("Keyword"),
                        "Type": st.column_config.TextColumn("Type"),
                        "Competitors": st.column_config.TextColumn("Competitors"),
                        "You Have?": st.column_config.TextColumn("You Have?")
                    },
                    hide_index=True,
                    use_container_width=True
                )

                # Quick select buttons
                st.write("**Quick Select:**")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("Top 5"):
                        st.session_state.selected_keywords = filtered[:5]
                        st.rerun()
                with col2:
                    if st.button("Top 10"):
                        st.session_state.selected_keywords = filtered[:10]
                        st.rerun()
                with col3:
                    if st.button("Top 20"):
                        st.session_state.selected_keywords = filtered[:20]
                        st.rerun()
                with col4:
                    if st.button("All Gaps"):
                        st.session_state.selected_keywords = [k for k in gap_keywords if k['you_have'] == 'No']
                        st.rerun()

                # Save selection from data editor
                selected_rows = edited_df[edited_df['Select'] == True]
                if len(selected_rows) > 0:
                    # Map back to original data
                    selected_keywords = []
                    for _, row in selected_rows.iterrows():
                        kw = row['Keyword']
                        for k in gap_keywords:
                            if k['keyword'] == kw:
                                selected_keywords.append(k)
                                break
                    st.session_state.selected_keywords = selected_keywords

                st.success(f"**{len(st.session_state.selected_keywords)} keywords selected** - Go to Tab 3 to generate content")
    
    # ============================================
    # TAB 3: GENERATE BLOGS
    # ============================================
    with tab3:
        if not st.session_state.selected_keywords:
            st.warning("⚠️ Please add keywords in Tab 2 first")
            st.info("💡 Go to Tab 2 and use 'Add Custom Keywords' to add your keywords, then come back here to generate content.")

        if st.session_state.selected_keywords:
            selected = st.session_state.selected_keywords

            st.subheader(f"{len(selected)} keywords selected")

            # Show selected keywords
            with st.expander("View selected keywords"):
                for kw in selected:
                    st.write(f"- **{kw['keyword']}** ({kw['type']}) - Occurrences: {kw.get('priority', 0)}")

            # ============================================
            # CONTENT TYPE SELECTION
            # ============================================
            st.markdown("### 📝 Content Type")

            content_type_options = {
                'auto': 'Auto-detect (based on keyword type)',
                'blog': 'Blog Post - Educational/informational content',
                'listicle': 'Listicle - List-based article (Top 10, Best X)',
                'tool_page': 'Tool/Product Page - Feature-focused landing page',
                'solution_page': 'Solution Page - Problem/solution focused',
                'comparison': 'Comparison - X vs Y detailed comparison',
                'alternative': 'Alternative Page - Best alternatives to X',
                'how_to': 'How-To Guide - Step-by-step tutorial'
            }

            selected_content_type = st.selectbox(
                "Select content type for generation",
                options=list(content_type_options.keys()),
                format_func=lambda x: content_type_options[x],
                index=0
            )

            # Show structure preview
            if selected_content_type != 'auto' and selected_content_type in CONTENT_TYPES:
                with st.expander(f"📋 View {CONTENT_TYPES[selected_content_type]['name']} Structure"):
                    st.code(CONTENT_TYPES[selected_content_type]['structure'], language='markdown')

            # ============================================
            # LEARN FROM SAMPLE URLs
            # ============================================
            st.markdown("### 🔗 Learn Structure from URLs (Optional)")
            st.caption("Provide sample URLs to learn content structure from existing pages")

            sample_url_input = st.text_area(
                "Sample URLs (one per line)",
                placeholder="https://example.com/blog/great-article\nhttps://competitor.com/resources/guide",
                height=80,
                key="sample_urls_input"
            )

            col_learn, col_clear = st.columns([1, 1])
            with col_learn:
                if st.button("🧠 Learn from URLs"):
                    if sample_url_input:
                        api_client = APIClient(st.session_state.api_key)
                        urls = [u.strip() for u in sample_url_input.split('\n') if u.strip()]

                        with st.spinner(f"Learning from {len(urls)} URLs..."):
                            learned = {}
                            for url in urls[:3]:  # Max 3 URLs
                                structure = learn_structure_from_url(api_client, url)
                                if structure:
                                    learned[url] = structure
                                    st.success(f"✅ Learned from: {url[:50]}...")

                            if learned:
                                st.session_state.sample_urls = learned
                            else:
                                st.warning("Could not learn from provided URLs")
                    else:
                        st.warning("Enter URLs first")

            with col_clear:
                if st.button("🗑️ Clear Learned Structures"):
                    st.session_state.sample_urls = {}
                    st.success("Cleared")

            # Show learned structures
            if st.session_state.get('sample_urls'):
                with st.expander(f"📚 Learned Structures ({len(st.session_state.sample_urls)} URLs)"):
                    for url, data in st.session_state.sample_urls.items():
                        st.markdown(f"**{url[:60]}...**")
                        st.code(data.get('template', 'No template')[:500], language='markdown')

            st.markdown("---")

            # Generation options
            st.markdown("### ⚙️ Generation Options")

            num_blogs = st.number_input("Number of blogs to generate", min_value=1, max_value=100, value=5, step=1)

            # Content format options
            col_opt1, col_opt2 = st.columns(2)

            with col_opt1:
                include_faqs = st.toggle("Include FAQs (4-5 questions)", value=True, help="Add a FAQ section at the end of each blog with 4-5 relevant questions and answers")

            with col_opt2:
                qa_format = st.toggle("Q&A Format (H2 as questions)", value=False, help="Structure the entire content as Q&A - each H2 heading will be a question that the content answers")

            if st.button("🚀 Generate Blogs", type="primary", use_container_width=True):
                api_client = APIClient(st.session_state.api_key)

                keywords_to_gen = selected[:num_blogs]

                progress = st.progress(0)
                status = st.empty()

                generated = []

                for i, kw_data in enumerate(keywords_to_gen):
                    status.text(f"✍️ Writing: {kw_data['keyword']}...")

                    try:
                        # Get company description for context
                        company_desc = st.session_state.get('company_description', '')

                        # Get custom structure if learned from URLs
                        custom_struct = ""
                        sample_urls = st.session_state.get('sample_urls', {})
                        if sample_urls:
                            # Use first learned structure as template
                            first_url = list(sample_urls.keys())[0]
                            custom_struct = sample_urls[first_url].get('template', '')

                        # Generate blog with content type, structure, and format options
                        blog = generate_blog(
                            api_client,
                            kw_data['keyword'],
                            kw_data['type'],
                            st.session_state.my_company_name,
                            st.session_state.company_style,
                            st.session_state.link_map,
                            kw_data.get('competitors', ''),
                            company_description=company_desc,
                            content_type=selected_content_type,
                            custom_structure=custom_struct,
                            include_faqs=include_faqs,
                            qa_format=qa_format
                        )

                        blog['keyword'] = kw_data['keyword']
                        blog['type'] = kw_data['type']
                        blog['content_type'] = selected_content_type

                        generated.append(blog)

                        st.success(f"✅ **{blog['title']}** ({blog['word_count']} words)")

                    except Exception as e:
                        st.error(f"❌ Failed: {kw_data['keyword']} - {str(e)}")

                    progress.progress((i + 1) / len(keywords_to_gen))
                    time.sleep(1)

                st.session_state.generated_blogs = generated

                status.text("✅ Generation complete!")

                st.markdown(f"""
                <div class="success-box">
                    <strong>🎉 Generated {len(generated)} blogs!</strong>
                </div>
                """, unsafe_allow_html=True)

            # Show generated blogs
            if st.session_state.generated_blogs:
                st.markdown("---")
                st.markdown("### 📄 Generated Blogs")

                for blog in st.session_state.generated_blogs:
                    with st.expander(f"📝 {blog.get('title', blog['keyword'])} ({blog.get('word_count', 0)} words)"):
                        st.markdown(f"**Keyword:** {blog['keyword']}")
                        st.markdown(f"**Type:** {blog['type']}")
                        st.markdown(f"**Meta Description:** {blog.get('meta_description', '')}")
                        st.markdown("---")
                        st.markdown(blog.get('content', '')[:3000] + "..." if len(blog.get('content', '')) > 3000 else blog.get('content', ''))
    
    # ============================================
    # TAB 4: EXPORT
    # ============================================
    with tab4:
        if not st.session_state.generated_blogs:
            st.warning("⚠️ Please generate blogs in Tab 3 first")
            return
        
        blogs = st.session_state.generated_blogs

        st.subheader(f"Export {len(blogs)} Blogs")

        st.write("**Choose Export Format:**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write("**Framer CMS**")
            st.caption("ZIP with CSV + cover images")

            framer_data = export_to_framer_format(blogs)

            st.download_button(
                "📥 Download for Framer",
                framer_data,
                f"framer_blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                "application/zip",
                use_container_width=True
            )

        with col2:
            st.write("**CSV**")
            st.caption("Basic spreadsheet format")

            csv_data = []
            for blog in blogs:
                csv_data.append({
                    'Keyword': blog['keyword'],
                    'Type': blog['type'],
                    'Title': blog.get('title', ''),
                    'Meta Description': blog.get('meta_description', ''),
                    'Word Count': blog.get('word_count', 0),
                    'Content': blog.get('content', '')
                })

            df = pd.DataFrame(csv_data)

            st.download_button(
                "📥 Download CSV",
                df.to_csv(index=False),
                f"blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col3:
            st.write("**JSON**")
            st.caption("Best for developers, APIs")

            json_data = json.dumps({
                'generated_at': datetime.now().isoformat(),
                'company': st.session_state.my_company_name,
                'total_blogs': len(blogs),
                'blogs': blogs
            }, indent=2, ensure_ascii=False)

            st.download_button(
                "📥 Download JSON",
                json_data,
                f"blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )

        with col4:
            st.write("**Notion**")
            st.caption("ZIP of .md files for Notion import")

            notion_data = export_to_notion_format(blogs)

            st.download_button(
                "📥 Download for Notion",
                notion_data,
                f"notion_blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                "application/zip",
                use_container_width=True
            )
        
        # Preview table
        st.markdown("---")
        st.markdown("### 📊 Export Preview")
        
        preview_df = pd.DataFrame([
            {
                'Title': b.get('title', ''),
                'Keyword': b['keyword'],
                'Type': b['type'],
                'Words': b.get('word_count', 0),
                'Meta': b.get('meta_description', '')[:50] + '...'
            }
            for b in blogs
        ])
        
        st.dataframe(preview_df, use_container_width=True)


if __name__ == "__main__":
    main()
