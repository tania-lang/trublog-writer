"""
Keyword Extractor Module
========================

Handles:
- Extracting keywords from URL slugs using AI
- Validating keywords are English and meaningful
- Finding gaps between competitor and company keywords
- Calculating keyword priority scores
"""

import re
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import anthropic


class KeywordExtractor:
    """AI-powered keyword extraction and analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def extract_from_urls(
        self,
        competitor_data: Dict[str, Dict],
        my_company_name: str
    ) -> Dict[str, Dict]:
        """
        Extract keywords from all competitor URLs
        
        Args:
            competitor_data: Dict with competitor name -> {domain, urls}
            my_company_name: Company name to replace in keywords
            
        Returns:
            Dict with keyword -> {frequency, competitors, type, urls}
        """
        all_keywords = defaultdict(lambda: {
            'frequency': 0,
            'competitors': set(),
            'type': 'Other',
            'urls': [],
            'score': 0
        })
        
        # Process each competitor
        for competitor_name, data in competitor_data.items():
            urls = data.get('urls', [])
            
            # Extract keywords in batches using Claude
            batch_size = 50
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                slugs = [url_data['slug'] for url_data in batch]
                
                keywords = self._extract_keywords_batch(slugs, competitor_name)
                
                for kw_data in keywords:
                    keyword = kw_data['keyword']
                    keyword_lower = keyword.lower()
                    
                    # Replace competitor name with placeholder if present
                    keyword_lower = keyword_lower.replace(competitor_name.lower(), '[company]')
                    
                    all_keywords[keyword_lower]['frequency'] += 1
                    all_keywords[keyword_lower]['competitors'].add(competitor_name)
                    all_keywords[keyword_lower]['type'] = kw_data.get('type', 'Other')
                    
                    if len(all_keywords[keyword_lower]['urls']) < 5:
                        all_keywords[keyword_lower]['urls'].append(kw_data.get('url', ''))
                    
                    # Update score
                    all_keywords[keyword_lower]['score'] = max(
                        all_keywords[keyword_lower]['score'],
                        kw_data.get('score', 0)
                    )
        
        # Convert sets to lists for JSON serialization
        result = {}
        for keyword, data in all_keywords.items():
            # Clean up the keyword
            clean_keyword = keyword.replace('[company]', my_company_name)
            
            result[clean_keyword] = {
                'frequency': data['frequency'],
                'competitors': list(data['competitors']),
                'competitor_count': len(data['competitors']),
                'type': data['type'],
                'urls': data['urls'],
                'score': data['score']
            }
        
        return result
    
    def _extract_keywords_batch(
        self,
        slugs: List[str],
        competitor_name: str
    ) -> List[Dict]:
        """
        Use Claude to extract meaningful keywords from URL slugs
        
        Args:
            slugs: List of URL slugs
            competitor_name: Name of competitor for context
            
        Returns:
            List of keyword dicts
        """
        slugs_text = '\n'.join(slugs[:50])  # Limit to 50
        
        prompt = f"""Analyze these URL slugs from {competitor_name}'s website and extract meaningful blog/content keywords.

URL Slugs:
{slugs_text}

For each slug that represents a blog post or content page, extract:
1. The main keyword/topic (2-5 words, in English)
2. The content type (Blog, Tool, Solution, Guide, Tutorial, Comparison, or Other)
3. A relevance score 1-10 (10 = highly valuable for SEO)

RULES:
- Only extract English keywords
- Skip slugs that are:
  - Product pages, pricing pages, about pages, contact pages
  - Login/signup pages
  - Language-specific paths (pt, es, de, fr, etc.)
  - Single random words or gibberish
  - Just numbers or codes
- Keywords should be meaningful phrases that make sense for blog topics
- Clean up the keyword: convert hyphens to spaces, proper capitalization

Return as a JSON array:
[
  {{"keyword": "Video Documentation Tools", "type": "Blog", "score": 8, "slug": "/blog/video-documentation-tools"}},
  {{"keyword": "How to Create Training Videos", "type": "Tutorial", "score": 9, "slug": "/guides/create-training-videos"}}
]

Return ONLY the JSON array. Skip slugs that don't represent valuable content keywords.
If no valid keywords found, return an empty array: []"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                import json
                keywords = json.loads(json_match.group())
                return keywords
            
            return []
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def extract_from_url_list(
        self,
        urls: List[Dict],
        source_name: str
    ) -> Set[str]:
        """
        Extract keywords from a list of URLs (for my company)
        
        Args:
            urls: List of URL dicts with slug
            source_name: Name identifier
            
        Returns:
            Set of keyword strings (lowercase)
        """
        keywords = set()
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            slugs = [url_data['slug'] for url_data in batch]
            
            extracted = self._extract_keywords_batch(slugs, source_name)
            
            for kw_data in extracted:
                keywords.add(kw_data['keyword'].lower())
        
        return keywords
    
    def find_gaps(
        self,
        competitor_keywords: Dict[str, Dict],
        my_keywords: Set[str],
        min_frequency: int = 2
    ) -> List[Dict]:
        """
        Find keyword gaps (competitors have, we don't)
        
        Args:
            competitor_keywords: Keywords from competitors
            my_keywords: Keywords we already have
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of gap keywords with metadata, sorted by priority
        """
        gaps = []
        
        for keyword, data in competitor_keywords.items():
            keyword_lower = keyword.lower()
            
            # Check if we already have this keyword
            has_keyword = any(
                self._keywords_similar(keyword_lower, my_kw)
                for my_kw in my_keywords
            )
            
            if has_keyword:
                continue
            
            # Calculate priority score
            # Priority = (frequency * 3) + (competitor_count * 5) + score
            priority = (
                (data['frequency'] * 3) +
                (data['competitor_count'] * 5) +
                data['score']
            )
            
            # Generate suggested title
            suggested_title = self._generate_title_suggestion(keyword, data['type'])
            
            gaps.append({
                'keyword': keyword.title(),  # Proper capitalization
                'type': data['type'],
                'frequency': data['frequency'],
                'competitor_count': data['competitor_count'],
                'competitors': ', '.join(data['competitors'][:5]),
                'priority': priority,
                'score': data['score'],
                'urls': data['urls'],
                'suggested_title': suggested_title
            })
        
        # Sort by priority (highest first)
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        
        # Filter by minimum frequency if specified
        if min_frequency > 1:
            gaps = [g for g in gaps if g['frequency'] >= min_frequency]
        
        return gaps
    
    def _keywords_similar(self, kw1: str, kw2: str) -> bool:
        """Check if two keywords are similar enough to be considered the same"""
        # Exact match
        if kw1 == kw2:
            return True
        
        # Normalize and compare
        kw1_normalized = re.sub(r'[^a-z0-9]', '', kw1)
        kw2_normalized = re.sub(r'[^a-z0-9]', '', kw2)
        
        if kw1_normalized == kw2_normalized:
            return True
        
        # Check if one contains the other
        if len(kw1_normalized) > 5 and len(kw2_normalized) > 5:
            if kw1_normalized in kw2_normalized or kw2_normalized in kw1_normalized:
                return True
        
        return False
    
    def _generate_title_suggestion(self, keyword: str, content_type: str) -> str:
        """Generate a suggested blog title based on keyword and type"""
        keyword_title = keyword.title()
        
        # Get current year
        from datetime import datetime
        current_year = datetime.now().year
        
        type_templates = {
            'Blog': [
                f"{keyword_title}: Complete Guide for {current_year}",
                f"Everything You Need to Know About {keyword_title}",
                f"{keyword_title} Explained: Tips and Best Practices"
            ],
            'Tool': [
                f"Best {keyword_title} in {current_year} (Top Picks Compared)",
                f"{keyword_title}: Features, Pricing, and Alternatives",
                f"Top {keyword_title} Tools That Actually Work"
            ],
            'Solution': [
                f"How to {keyword_title}: A Practical Guide",
                f"{keyword_title} Made Easy: Step by Step",
                f"Why {keyword_title} Matters and How to Get Started"
            ],
            'Guide': [
                f"The Ultimate Guide to {keyword_title}",
                f"{keyword_title}: A Comprehensive Guide for {current_year}",
                f"Mastering {keyword_title}: Expert Tips and Strategies"
            ],
            'Tutorial': [
                f"How to {keyword_title}: Complete Tutorial",
                f"{keyword_title} Tutorial for Beginners",
                f"Learn {keyword_title}: Step by Step Guide"
            ],
            'Comparison': [
                f"{keyword_title}: Complete Comparison Guide",
                f"Best {keyword_title} Compared ({current_year})",
                f"{keyword_title} Showdown: Which One is Right for You?"
            ]
        }
        
        templates = type_templates.get(content_type, type_templates['Blog'])
        
        # Return first template
        return templates[0]
    
    def validate_keywords_with_ai(self, keywords: List[Dict]) -> List[Dict]:
        """
        Use Claude to validate and improve keyword list
        
        Args:
            keywords: List of keyword dicts
            
        Returns:
            Validated and improved keyword list
        """
        keywords_text = '\n'.join([
            f"- {kw['keyword']} (Type: {kw['type']}, Priority: {kw['priority']})"
            for kw in keywords[:50]
        ])
        
        prompt = f"""Review these extracted keywords for SEO blog topics.

Keywords:
{keywords_text}

For each keyword, assess:
1. Is it in proper English? (reject non-English)
2. Does it make sense as a blog topic? (reject gibberish, random letters, single words)
3. Is the type classification correct?
4. Should the keyword be rephrased for better SEO?

Return a JSON array with validated keywords:
[
  {{"keyword": "Original or Improved Keyword", "type": "Corrected Type", "valid": true, "reason": "Good topic"}},
  {{"keyword": "Bad Keyword", "type": "Other", "valid": false, "reason": "Not English"}}
]

Be strict - only approve keywords that would make good blog topics.
Return ONLY the JSON array."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                import json
                validated = json.loads(json_match.group())
                
                # Merge validation results back
                validated_map = {v['keyword'].lower(): v for v in validated}
                
                result = []
                for kw in keywords:
                    kw_lower = kw['keyword'].lower()
                    if kw_lower in validated_map:
                        validation = validated_map[kw_lower]
                        if validation.get('valid', False):
                            kw['keyword'] = validation.get('keyword', kw['keyword'])
                            kw['type'] = validation.get('type', kw['type'])
                            result.append(kw)
                    else:
                        # Keep if not in validation (wasn't checked)
                        result.append(kw)
                
                return result
            
            return keywords
            
        except Exception as e:
            print(f"Error validating keywords: {e}")
            return keywords
