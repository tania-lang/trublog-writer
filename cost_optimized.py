"""
SEO Blog Generator - COST OPTIMIZED VERSION
============================================

Cost Reduction Strategies:
1. Use Claude Haiku (cheapest) for simple tasks
2. Use Claude Sonnet only for blog generation
3. Batch API calls to reduce overhead
4. Cache results to avoid repeat calls
5. Local keyword extraction first, AI only for validation
6. Reduce token usage in prompts

Pricing (per 1M tokens):
- Haiku: $0.25 input / $1.25 output (10x cheaper than Sonnet)
- Sonnet: $3 input / $15 output

Estimated costs with optimization:
- 10 blogs: ~$0.50-1.00 (down from $2-3)
"""

import requests
import re
import json
import os
from typing import List, Dict, Set, Optional
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import hashlib
import anthropic
from bs4 import BeautifulSoup


# ============================================
# CACHE MANAGER - Avoid repeat API calls
# ============================================

class CacheManager:
    """Simple file-based cache to avoid repeat API calls"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_key(self, data: str) -> str:
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[dict]:
        cache_file = self.cache_dir / f"{self._get_key(key)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def set(self, key: str, value: dict):
        cache_file = self.cache_dir / f"{self._get_key(key)}.json"
        with open(cache_file, 'w') as f:
            json.dump(value, f)
    
    def clear(self):
        for f in self.cache_dir.glob("*.json"):
            f.unlink()


# ============================================
# COST-OPTIMIZED API CLIENT
# ============================================

class OptimizedAPIClient:
    """
    Smart API client that:
    - Uses Haiku for simple tasks (cheap)
    - Uses Sonnet only for complex generation
    - Batches requests where possible
    - Caches results
    """
    
    # Model pricing per 1M tokens
    PRICING = {
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        'claude-sonnet-4-20250514': {'input': 3.0, 'output': 15.0}
    }
    
    HAIKU = 'claude-3-haiku-20240307'
    SONNET = 'claude-sonnet-4-20250514'
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cache = CacheManager()
        self.total_cost = 0.0
        self.call_count = 0
    
    def call_haiku(self, prompt: str, max_tokens: int = 1000, use_cache: bool = True) -> str:
        """Use Haiku for simple/cheap tasks"""
        return self._call(self.HAIKU, prompt, max_tokens, use_cache)
    
    def call_sonnet(self, prompt: str, max_tokens: int = 4000, use_cache: bool = False) -> str:
        """Use Sonnet for complex generation"""
        return self._call(self.SONNET, prompt, max_tokens, use_cache)
    
    def _call(self, model: str, prompt: str, max_tokens: int, use_cache: bool) -> str:
        # Check cache
        cache_key = f"{model}:{prompt[:500]}"
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached.get('response', '')
        
        # Make API call
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        
        # Track costs
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * self.PRICING[model]['input'] / 1_000_000 +
                output_tokens * self.PRICING[model]['output'] / 1_000_000)
        self.total_cost += cost
        self.call_count += 1
        
        # Cache result
        if use_cache:
            self.cache.set(cache_key, {'response': result})
        
        return result
    
    def get_cost_report(self) -> str:
        return f"API Calls: {self.call_count} | Total Cost: ${self.total_cost:.4f}"


# ============================================
# LOCAL KEYWORD EXTRACTION (NO API COST)
# ============================================

class LocalKeywordExtractor:
    """
    Extract keywords locally without API calls
    Only use AI for validation of final list
    """
    
    # Common English stop words
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'what', 'which', 'who', 'whom', 'www', 'http', 'https',
        'com', 'org', 'net', 'html', 'php', 'page', 'post', 'blog', 'article'
    }
    
    # Language codes to filter
    LANGUAGE_CODES = {
        'pt', 'br', 'es', 'de', 'fr', 'it', 'nl', 'ja', 'jp', 'ko', 'kr',
        'zh', 'cn', 'ru', 'ar', 'pl', 'tr', 'sv', 'da', 'fi', 'no', 'cs',
        'hu', 'ro', 'uk', 'el', 'he', 'vi', 'th', 'id', 'ms', 'hi', 'ptbr'
    }
    
    # High-value keyword indicators
    BLOG_WORDS = {'best', 'top', 'guide', 'tips', 'review', 'comparison', 'alternative', 'vs', 'versus'}
    TOOL_WORDS = {'generator', 'creator', 'maker', 'builder', 'tool', 'software', 'app', 'free', 'online'}
    HOW_TO_WORDS = {'how', 'tutorial', 'learn', 'create', 'make', 'build', 'setup', 'install'}
    
    def extract_from_slug(self, slug: str) -> Optional[Dict]:
        """Extract keyword from URL slug locally"""
        if not slug or slug == '/':
            return None
        
        # Clean slug
        slug = slug.lower().strip('/')
        parts = slug.split('/')
        
        # Skip non-English paths
        for part in parts:
            if part in self.LANGUAGE_CODES:
                return None
            if re.match(r'^[a-z]{2}-[a-z]{2}$', part):
                return None
        
        # Get the most meaningful part (usually last)
        best_part = None
        best_score = 0
        
        for part in parts:
            # Skip short parts
            if len(part) < 5:
                continue
            
            # Split on hyphens/underscores
            words = re.split(r'[-_]', part)
            words = [w for w in words if len(w) >= 3 and w not in self.STOP_WORDS]
            
            if len(words) < 2:
                continue
            
            # Score this part
            score = len(words)
            
            for w in words:
                if w in self.BLOG_WORDS:
                    score += 3
                if w in self.TOOL_WORDS:
                    score += 4
                if w in self.HOW_TO_WORDS:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_part = words
        
        if not best_part or best_score < 3:
            return None
        
        # Check for vowels (basic English check)
        keyword = ' '.join(best_part)
        if not any(c in keyword for c in 'aeiou'):
            return None
        
        # Determine type
        kw_type = 'Blog'
        for w in best_part:
            if w in self.TOOL_WORDS:
                kw_type = 'Tool'
                break
            if w in self.HOW_TO_WORDS:
                kw_type = 'How-To'
                break
        
        # Title case
        keyword = ' '.join(w.capitalize() for w in best_part)
        
        return {
            'keyword': keyword,
            'type': kw_type,
            'score': best_score
        }
    
    def extract_batch(self, urls: List[Dict]) -> Dict[str, Dict]:
        """Extract keywords from multiple URLs locally"""
        keywords = defaultdict(lambda: {
            'frequency': 0,
            'urls': [],
            'type': 'Blog',
            'score': 0
        })
        
        for url_data in urls:
            result = self.extract_from_slug(url_data.get('slug', ''))
            if result:
                kw_lower = result['keyword'].lower()
                keywords[kw_lower]['frequency'] += 1
                keywords[kw_lower]['type'] = result['type']
                keywords[kw_lower]['score'] = max(keywords[kw_lower]['score'], result['score'])
                if len(keywords[kw_lower]['urls']) < 3:
                    keywords[kw_lower]['urls'].append(url_data.get('url', ''))
        
        return dict(keywords)


# ============================================
# COST-OPTIMIZED SITEMAP SCRAPER
# ============================================

class OptimizedSitemapScraper:
    """Sitemap scraper with minimal API usage"""
    
    def __init__(self, api_client: OptimizedAPIClient):
        self.api = api_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SEOBot/1.0)'
        })
    
    def find_domains(self, company_names: List[str]) -> Dict[str, str]:
        """Find domains using Haiku (cheap) with caching"""
        # Batch all companies in one call
        prompt = f"""Find website domains for: {', '.join(company_names)}
Return JSON only: {{"Company": "domain.com"}}"""
        
        response = self.api.call_haiku(prompt, max_tokens=500, use_cache=True)
        
        try:
            match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return {}
    
    def fetch_sitemap(self, domain: str) -> List[Dict]:
        """Fetch sitemap (no API needed)"""
        domain = domain.replace('https://', '').replace('http://', '').strip('/')
        base = f"https://{domain}"
        
        urls = []
        sitemaps_to_check = [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/wp-sitemap.xml",
            f"{base}/sitemap1.xml"
        ]
        
        # Check robots.txt
        try:
            robots = self.session.get(f"{base}/robots.txt", timeout=10)
            if robots.status_code == 200:
                matches = re.findall(r'Sitemap:\s*(.+)', robots.text, re.I)
                sitemaps_to_check = [m.strip() for m in matches] + sitemaps_to_check
        except:
            pass
        
        processed = set()
        
        for sitemap_url in sitemaps_to_check[:10]:  # Limit to prevent infinite loops
            if sitemap_url in processed:
                continue
            processed.add(sitemap_url)
            
            try:
                resp = self.session.get(sitemap_url, timeout=15)
                if resp.status_code != 200:
                    continue
                
                content = resp.text
                
                # Check for sitemap index
                if '<sitemapindex' in content:
                    child_urls = re.findall(r'<loc>([^<]+\.xml[^<]*)</loc>', content)
                    for child in child_urls[:20]:
                        if child not in processed:
                            sitemaps_to_check.append(child)
                
                # Extract page URLs
                page_urls = re.findall(r'<loc>([^<]+)</loc>', content)
                for url in page_urls:
                    if '.xml' in url:
                        continue
                    
                    # Skip non-English
                    if any(f'/{lang}/' in url.lower() for lang in ['pt', 'es', 'de', 'fr', 'it', 'ja', 'ko', 'zh']):
                        continue
                    
                    slug = url.replace(base, '').split('?')[0]
                    urls.append({'url': url, 'slug': slug, 'domain': domain})
                
            except:
                continue
            
            if len(urls) > 2000:
                break
        
        # Deduplicate
        seen = set()
        unique = []
        for u in urls:
            if u['url'] not in seen:
                seen.add(u['url'])
                unique.append(u)
        
        return unique


# ============================================
# COST-OPTIMIZED CONTENT ANALYZER
# ============================================

class OptimizedContentAnalyzer:
    """Content analyzer with minimal API usage"""
    
    def __init__(self, api_client: OptimizedAPIClient):
        self.api = api_client
        self.session = requests.Session()
    
    def learn_style_quick(self, urls: List[Dict]) -> Dict:
        """Learn style from just 5 pages using Haiku"""
        # Fetch 5 pages
        contents = []
        for url_data in urls[:5]:
            try:
                resp = self.session.get(url_data['url'], timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for tag in soup(['script', 'style', 'nav', 'footer']):
                        tag.decompose()
                    text = soup.get_text(' ', strip=True)[:1500]
                    contents.append(text)
            except:
                continue
        
        if not contents:
            return self._default_style()
        
        # Single Haiku call for style analysis
        prompt = f"""Analyze writing style from these excerpts. Return JSON:
{{"tone": "...", "voice": "...", "style_notes": "..."}}

Excerpts:
{contents[0][:800]}
---
{contents[1][:800] if len(contents) > 1 else ''}"""
        
        response = self.api.call_haiku(prompt, max_tokens=300, use_cache=True)
        
        try:
            match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return self._default_style()
    
    def _default_style(self) -> Dict:
        return {
            "tone": "professional but friendly",
            "voice": "second person",
            "style_notes": "clear, practical, uses examples"
        }
    
    def build_link_map_local(self, urls: List[Dict]) -> Dict[str, str]:
        """Build link map locally without API"""
        link_map = {}
        
        for url_data in urls:
            slug = url_data.get('slug', '').lower().strip('/')
            if not slug or slug == '/':
                continue
            
            # Extract keywords from slug
            parts = slug.split('/')
            for part in parts:
                words = re.split(r'[-_]', part)
                words = [w for w in words if len(w) >= 4]
                
                if len(words) >= 2:
                    keyword = ' '.join(words)
                    link_map[keyword] = url_data['url']
        
        return link_map


# ============================================
# COST-OPTIMIZED BLOG GENERATOR
# ============================================

class OptimizedBlogGenerator:
    """Blog generator optimized for cost"""
    
    def __init__(
        self,
        api_client: OptimizedAPIClient,
        company_name: str,
        company_style: Dict = None,
        link_map: Dict = None
    ):
        self.api = api_client
        self.company_name = company_name
        self.company_style = company_style or {}
        self.link_map = link_map or {}
        self.current_year = datetime.now().year
    
    def generate_blog(self, keyword: str, keyword_type: str = "Blog") -> Dict:
        """Generate blog using Sonnet (only place we use expensive model)"""
        
        # Build concise prompt (fewer tokens = lower cost)
        prompt = self._build_efficient_prompt(keyword, keyword_type)
        
        # Use Sonnet for actual generation
        response = self.api.call_sonnet(prompt, max_tokens=6000, use_cache=False)
        
        # Parse response
        blog = self._parse_response(response, keyword)
        
        # Post-process locally (no API)
        blog['content'] = self._clean_content(blog['content'])
        blog['word_count'] = len(blog['content'].split())
        
        return blog
    
    def _build_efficient_prompt(self, keyword: str, keyword_type: str) -> str:
        """Build a concise but effective prompt"""
        
        style_note = self.company_style.get('tone', 'professional but friendly')
        
        # Get relevant internal links (max 5)
        links = []
        kw_words = set(keyword.lower().split())
        for link_kw, url in list(self.link_map.items())[:50]:
            if any(w in link_kw for w in kw_words):
                links.append(f"- {link_kw}: {url}")
                if len(links) >= 5:
                    break
        
        links_text = '\n'.join(links) if links else "None"
        
        prompt = f"""Write a 2500+ word blog for {self.company_name}.

KEYWORD: {keyword}
TYPE: {keyword_type}
YEAR: {self.current_year}
TONE: {style_note}

INTERNAL LINKS TO USE:
{links_text}

RULES:
- 2500+ words minimum
- No dashes (—, –). Use commas.
- No AI phrases: "in today's world", "let's dive in", "it's worth noting", "leverage", "utilize", "synergy", "delve"
- Use contractions (don't, can't, it's)
- Vary sentence length
- Include practical examples
- Add 5 FAQs at end
- Use {self.current_year} for current year references
- Add comparison table where relevant
- Include internal links naturally

FORMAT:
TITLE: [title]
META: [150 char description]
CONTENT:
[markdown content]"""

        return prompt
    
    def _parse_response(self, response: str, keyword: str) -> Dict:
        """Parse blog response"""
        result = {
            'title': f"{keyword} Guide {self.current_year}",
            'meta_description': f"Learn about {keyword}.",
            'content': response
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
        
        return result
    
    def _clean_content(self, content: str) -> str:
        """Clean content locally (no API cost)"""
        if not content:
            return content
        
        # Remove dashes
        content = re.sub(r'\s*[—–]\s*', ', ', content)
        content = re.sub(r'\s+-\s+', ', ', content)
        
        # Remove AI phrases
        ai_phrases = [
            r"in today's (?:world|digital|fast)",
            r"let's (?:dive|explore|delve)",
            r"it's (?:worth noting|important to note)",
            r"at the end of the day",
            r"first and foremost",
            r"without further ado",
        ]
        for phrase in ai_phrases:
            content = re.sub(phrase, '', content, flags=re.I)
        
        # Update old years
        for year in ['2024', '2023', '2022']:
            content = re.sub(rf'\b{year}\b', str(self.current_year), content)
        
        # Clean up
        content = re.sub(r',\s*,', ',', content)
        content = re.sub(r'\s{2,}', ' ', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()


# ============================================
# MAIN OPTIMIZED GENERATOR CLASS
# ============================================

class CostOptimizedBlogGenerator:
    """
    Main class with all cost optimizations
    
    Estimated costs:
    - Domain finding: ~$0.001 per batch (Haiku + cache)
    - Keyword extraction: $0 (local)
    - Style learning: ~$0.002 (Haiku + cache)
    - Blog generation: ~$0.05-0.10 per blog (Sonnet)
    
    Total for 10 blogs: ~$0.50-1.00
    """
    
    def __init__(self, api_key: str):
        self.api = OptimizedAPIClient(api_key)
        self.scraper = OptimizedSitemapScraper(self.api)
        self.local_extractor = LocalKeywordExtractor()
        self.analyzer = OptimizedContentAnalyzer(self.api)
        
        self.my_company_name = ""
        self.my_urls = []
        self.competitor_data = {}
        self.company_style = {}
        self.link_map = {}
        self.keywords = []
        self.generated_blogs = []
    
    def setup(self, company_name: str, company_domain: str):
        """Setup company info"""
        self.my_company_name = company_name
        
        print(f"📥 Fetching {company_domain} sitemap...")
        self.my_urls = self.scraper.fetch_sitemap(company_domain)
        print(f"   Found {len(self.my_urls)} URLs")
        
        print(f"📖 Learning style (quick)...")
        self.company_style = self.analyzer.learn_style_quick(self.my_urls)
        
        print(f"🔗 Building link map (local)...")
        self.link_map = self.analyzer.build_link_map_local(self.my_urls)
        print(f"   {len(self.link_map)} link keywords")
    
    def add_competitors(self, names: List[str]):
        """Add and analyze competitors"""
        print(f"\n🔍 Finding competitor domains...")
        domains = self.scraper.find_domains(names)
        
        print(f"📥 Fetching competitor sitemaps...")
        for name, domain in domains.items():
            if domain:
                print(f"   {name}: {domain}...", end=" ")
                urls = self.scraper.fetch_sitemap(domain)
                self.competitor_data[name] = {'domain': domain, 'urls': urls}
                print(f"{len(urls)} URLs")
    
    def extract_keywords(self, min_frequency: int = 2) -> List[Dict]:
        """Extract keywords locally, validate with AI only if needed"""
        print(f"\n🔑 Extracting keywords (local)...")
        
        # Extract from competitors locally
        all_keywords = defaultdict(lambda: {
            'frequency': 0,
            'competitors': set(),
            'type': 'Blog',
            'score': 0
        })
        
        for comp_name, data in self.competitor_data.items():
            comp_keywords = self.local_extractor.extract_batch(data['urls'])
            
            for kw, kw_data in comp_keywords.items():
                all_keywords[kw]['frequency'] += kw_data['frequency']
                all_keywords[kw]['competitors'].add(comp_name)
                all_keywords[kw]['type'] = kw_data['type']
                all_keywords[kw]['score'] = max(all_keywords[kw]['score'], kw_data['score'])
        
        # Extract from my site
        my_keywords = set(self.local_extractor.extract_batch(self.my_urls).keys())
        
        # Find gaps
        gaps = []
        for kw, data in all_keywords.items():
            if kw.lower() in my_keywords:
                continue
            
            if data['frequency'] < min_frequency:
                continue
            
            priority = (data['frequency'] * 3) + (len(data['competitors']) * 5) + data['score']
            
            gaps.append({
                'keyword': kw.title(),
                'type': data['type'],
                'frequency': data['frequency'],
                'competitor_count': len(data['competitors']),
                'competitors': ', '.join(data['competitors']),
                'priority': priority
            })
        
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        self.keywords = gaps
        
        print(f"   Found {len(gaps)} keyword gaps")
        return gaps
    
    def generate_blogs(self, keywords: List[Dict], max_blogs: int = 10) -> List[Dict]:
        """Generate blogs (this is where most cost occurs)"""
        generator = OptimizedBlogGenerator(
            api_client=self.api,
            company_name=self.my_company_name,
            company_style=self.company_style,
            link_map=self.link_map
        )
        
        self.generated_blogs = []
        
        for i, kw in enumerate(keywords[:max_blogs]):
            print(f"\n[{i+1}/{min(len(keywords), max_blogs)}] Generating: {kw['keyword']}")
            
            try:
                blog = generator.generate_blog(kw['keyword'], kw['type'])
                blog['keyword'] = kw['keyword']
                blog['type'] = kw['type']
                self.generated_blogs.append(blog)
                print(f"   ✓ {blog['title']} ({blog['word_count']} words)")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        return self.generated_blogs
    
    def export(self, output_dir: str = "output"):
        """Export blogs"""
        Path(output_dir).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON
        json_path = f"{output_dir}/blogs_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                'generated_at': timestamp,
                'cost': self.api.get_cost_report(),
                'blogs': self.generated_blogs
            }, f, indent=2)
        print(f"✓ Saved to {json_path}")
        
        # CSV
        csv_path = f"{output_dir}/blogs_{timestamp}.csv"
        with open(csv_path, 'w') as f:
            f.write("Keyword,Type,Title,Meta,WordCount,Content\n")
            for blog in self.generated_blogs:
                content = blog.get('content', '').replace('"', '""')
                f.write(f'"{blog["keyword"]}","{blog["type"]}","{blog["title"]}","{blog["meta_description"]}",{blog["word_count"]},"{content}"\n')
        print(f"✓ Saved to {csv_path}")
    
    def print_cost_report(self):
        """Print cost report"""
        print(f"\n💰 {self.api.get_cost_report()}")


# ============================================
# CLI ENTRY POINT
# ============================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cost-Optimized SEO Blog Generator")
    parser.add_argument('--api-key', required=True, help='Claude API key')
    parser.add_argument('--company', required=True, help='Your company name')
    parser.add_argument('--domain', required=True, help='Your domain')
    parser.add_argument('--competitors', nargs='+', required=True, help='Competitor names')
    parser.add_argument('--max-blogs', type=int, default=10, help='Max blogs to generate')
    parser.add_argument('--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("COST-OPTIMIZED SEO BLOG GENERATOR")
    print("=" * 50)
    
    gen = CostOptimizedBlogGenerator(args.api_key)
    
    # Setup
    gen.setup(args.company, args.domain)
    
    # Competitors
    gen.add_competitors(args.competitors)
    
    # Keywords
    keywords = gen.extract_keywords()
    
    # Show top keywords
    print(f"\nTop {min(20, len(keywords))} keywords:")
    for i, kw in enumerate(keywords[:20]):
        print(f"  {i+1}. {kw['keyword']} (Priority: {kw['priority']})")
    
    # Generate
    print(f"\n✨ Generating {args.max_blogs} blogs...")
    gen.generate_blogs(keywords, max_blogs=args.max_blogs)
    
    # Export
    gen.export(args.output)
    
    # Cost report
    gen.print_cost_report()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
