"""
Content Analyzer Module
=======================

Handles:
- Learning company writing style from existing content
- Building internal link maps
- Extracting product context
- Analyzing content structure
"""

import re
from typing import List, Dict, Optional, Set
from collections import defaultdict
import anthropic
from bs4 import BeautifulSoup
import requests


class ContentAnalyzer:
    """Analyzes company content to learn style and context"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SEOBlogBot/1.0)'
        })
    
    def learn_company_style(self, urls: List[Dict], sample_size: int = 20) -> Dict:
        """
        Learn writing style from company's existing content
        
        Args:
            urls: List of URL dicts
            sample_size: Number of pages to analyze
            
        Returns:
            Dict with style analysis
        """
        # Fetch sample content
        contents = []
        for url_data in urls[:sample_size]:
            content = self._fetch_page_content(url_data['url'])
            if content and len(content) > 500:
                contents.append({
                    'url': url_data['url'],
                    'content': content[:5000]  # Limit per page
                })
        
        if not contents:
            return self._default_style()
        
        # Analyze with Claude
        sample_text = '\n\n---\n\n'.join([
            f"URL: {c['url']}\nContent: {c['content'][:2000]}"
            for c in contents[:10]
        ])
        
        prompt = f"""Analyze this company's blog content and extract their writing style characteristics.

Sample Content:
{sample_text}

Analyze and return a JSON object with:

1. "tone": Overall tone (e.g., "professional but friendly", "technical", "casual", "formal")
2. "voice": First person, second person, third person, or mixed
3. "sentence_structure": Description of typical sentence patterns
4. "paragraph_length": Short, medium, long, or varied
5. "use_of_headers": How they structure with H2/H3 headers
6. "formatting_style": Use of bullets, numbered lists, bold, etc.
7. "cta_style": How they include calls to action
8. "technical_level": Beginner, intermediate, advanced, or mixed
9. "unique_phrases": List of phrases or expressions they commonly use
10. "topics_covered": Main topic areas they write about
11. "internal_linking_style": How they link to other pages
12. "content_length": Typical article length (short/medium/long)
13. "brand_voice_keywords": Words that define their brand voice

Return ONLY the JSON object, no explanation."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                style = json.loads(json_match.group())
                return style
            
            return self._default_style()
            
        except Exception as e:
            print(f"Error learning style: {e}")
            return self._default_style()
    
    def _default_style(self) -> Dict:
        """Return default style if analysis fails"""
        return {
            "tone": "professional but approachable",
            "voice": "second person (you/your)",
            "sentence_structure": "varied, mix of short and long",
            "paragraph_length": "medium (3-5 sentences)",
            "use_of_headers": "clear H2 sections with occasional H3",
            "formatting_style": "moderate use of bullets and bold",
            "cta_style": "soft CTAs woven into content",
            "technical_level": "intermediate",
            "unique_phrases": [],
            "topics_covered": [],
            "internal_linking_style": "natural, contextual links",
            "content_length": "long (2000+ words)",
            "brand_voice_keywords": []
        }
    
    def build_link_map(self, urls: List[Dict]) -> Dict[str, Dict]:
        """
        Build a map of pages and their key topics for internal linking
        
        Args:
            urls: List of URL dicts
            
        Returns:
            Dict mapping keywords/topics to URLs
        """
        link_map = defaultdict(list)
        
        # Process URLs in batches with Claude
        batch_size = 30
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            
            urls_text = '\n'.join([
                f"- {url_data['url']} (slug: {url_data['slug']})"
                for url_data in batch
            ])
            
            prompt = f"""Analyze these URLs and extract the main topic/keyword each page is about.

URLs:
{urls_text}

For each URL, identify 1-3 keywords that describe what the page is about.
These keywords will be used for internal linking.

Return a JSON object mapping URLs to their keywords:
{{
  "https://example.com/blog/video-tools": ["video tools", "video software", "screen recording"],
  "https://example.com/features/ai-avatar": ["AI avatar", "avatar generator", "virtual presenter"]
}}

Return ONLY the JSON object."""

            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = response.content[0].text
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    import json
                    batch_map = json.loads(json_match.group())
                    
                    for url, keywords in batch_map.items():
                        for keyword in keywords:
                            keyword_lower = keyword.lower()
                            if url not in [l['url'] for l in link_map[keyword_lower]]:
                                link_map[keyword_lower].append({
                                    'url': url,
                                    'anchor_text': keyword
                                })
                
            except Exception as e:
                print(f"Error building link map: {e}")
                continue
        
        return dict(link_map)
    
    def extract_product_context(self, urls: List[Dict]) -> Dict:
        """
        Extract product information and context from company pages
        
        Args:
            urls: List of URL dicts
            
        Returns:
            Dict with product context
        """
        # Find product/feature pages
        product_urls = []
        for url_data in urls:
            slug = url_data['slug'].lower()
            if any(term in slug for term in [
                'feature', 'product', 'solution', 'platform',
                'pricing', 'demo', 'how-it-works', 'use-case'
            ]):
                product_urls.append(url_data)
        
        # Fetch and analyze product pages
        product_content = []
        for url_data in product_urls[:10]:
            content = self._fetch_page_content(url_data['url'])
            if content:
                product_content.append({
                    'url': url_data['url'],
                    'content': content[:3000]
                })
        
        if not product_content:
            return {}
        
        # Analyze with Claude
        content_text = '\n\n---\n\n'.join([
            f"URL: {c['url']}\nContent: {c['content']}"
            for c in product_content[:5]
        ])
        
        prompt = f"""Analyze this product/company content and extract key information.

Content:
{content_text}

Extract and return a JSON object with:

1. "product_name": Main product name
2. "product_description": One paragraph description
3. "key_features": List of main features (max 10)
4. "use_cases": List of use cases (max 10)
5. "target_audience": Who the product is for
6. "value_propositions": Key value props (max 5)
7. "competitors_mentioned": Any competitors mentioned
8. "integrations": Any integrations mentioned
9. "pricing_model": If mentioned (free, freemium, paid, etc.)
10. "cta_phrases": Common CTA phrases used

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
            
            return {}
            
        except Exception as e:
            print(f"Error extracting product context: {e}")
            return {}
    
    def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch and extract text content from a page"""
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
                tag.decompose()
            
            # Try to find main content
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find(class_=re.compile(r'content|post|article|blog|entry', re.I)) or
                soup.find(id=re.compile(r'content|post|article|blog|entry', re.I)) or
                soup.find('body')
            )
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
                return text
            
            return None
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def get_existing_blog_topics(self, urls: List[Dict]) -> List[str]:
        """
        Get list of existing blog topics from URLs
        
        Args:
            urls: List of URL dicts
            
        Returns:
            List of topic strings
        """
        # Filter for blog URLs
        blog_urls = []
        for url_data in urls:
            slug = url_data['slug'].lower()
            if '/blog/' in slug or '/posts/' in slug or '/articles/' in slug:
                blog_urls.append(url_data)
        
        if not blog_urls:
            return []
        
        # Extract topics with Claude
        slugs_text = '\n'.join([url_data['slug'] for url_data in blog_urls[:100]])
        
        prompt = f"""Extract the main topic from each of these blog URL slugs.

Slugs:
{slugs_text}

Return a JSON array of topic strings (the main subject of each blog):
["topic 1", "topic 2", "topic 3"]

Clean up the topics:
- Convert hyphens to spaces
- Proper capitalization
- Remove dates, numbers, etc.

Return ONLY the JSON array."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
            
            return []
            
        except Exception as e:
            print(f"Error getting blog topics: {e}")
            return []
