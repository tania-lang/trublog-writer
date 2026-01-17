"""
Sitemap Scraper Module
======================

Handles:
- Finding domains from company names using Claude
- Fetching sitemaps from domains
- Extracting URLs from XML sitemaps
- Handling sitemap indexes
"""

import requests
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional
import time
import anthropic
from bs4 import BeautifulSoup


class SitemapScraper:
    """Scrapes sitemaps and finds domains using AI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SEOBlogBot/1.0; +https://example.com/bot)'
        })
        
        self.sitemap_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-index.xml',
            '/wp-sitemap.xml',
            '/sitemap1.xml',
            '/post-sitemap.xml',
            '/page-sitemap.xml',
            '/blog-sitemap.xml',
            '/news-sitemap.xml',
            '/sitemap/sitemap.xml'
        ]
    
    def find_domains(self, company_names: List[str]) -> Dict[str, str]:
        """
        Use Claude to find official domains for company names
        
        Args:
            company_names: List of company names
            
        Returns:
            Dict mapping company name to domain
        """
        prompt = f"""Find the official primary website domain for each of these companies. 
Return ONLY the main English website domain (not localized versions like .de, .fr, etc.).

Companies:
{chr(10).join(f"- {name}" for name in company_names)}

Return your response as a JSON object with company names as keys and domains as values.
Example format:
{{"Company Name": "companydomain.com", "Another Company": "anotherdomain.io"}}

Important:
- Only return the domain (e.g., "example.com"), not full URLs
- Use the primary English domain
- If a company has multiple domains, use the main product/marketing site
- Return ONLY the JSON, no explanation"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                import json
                domains = json.loads(json_match.group())
                return domains
            
            return {}
            
        except Exception as e:
            print(f"Error finding domains: {e}")
            return {}
    
    def find_subdomains(self, domain: str) -> List[str]:
        """
        Use Claude to find common subdomains for a domain
        
        Args:
            domain: Main domain
            
        Returns:
            List of subdomains
        """
        prompt = f"""What are the common subdomains for {domain}?
        
Consider subdomains like:
- blog.{domain}
- docs.{domain}
- help.{domain}
- support.{domain}
- www.{domain}
- app.{domain}
- api.{domain}

Return ONLY a JSON array of subdomains that likely exist for this company.
Example: ["blog.example.com", "docs.example.com", "help.example.com"]

Return ONLY the JSON array, no explanation."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                import json
                subdomains = json.loads(json_match.group())
                
                # Verify subdomains exist
                valid_subdomains = []
                for subdomain in subdomains:
                    if self._check_domain_exists(subdomain):
                        valid_subdomains.append(subdomain)
                
                return valid_subdomains
            
            return []
            
        except Exception as e:
            print(f"Error finding subdomains: {e}")
            return []
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if a domain is accessible"""
        try:
            response = self.session.head(
                f"https://{domain}",
                timeout=5,
                allow_redirects=True
            )
            return response.status_code < 400
        except:
            return False
    
    def fetch_sitemap(self, domain: str) -> List[Dict]:
        """
        Fetch all URLs from a domain's sitemap
        
        Args:
            domain: Domain to fetch sitemap from
            
        Returns:
            List of dicts with url and slug
        """
        domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
        base_url = f"https://{domain}"
        
        all_urls = []
        processed_sitemaps = set()
        sitemap_queue = []
        
        # Try robots.txt first
        robots_sitemaps = self._get_sitemaps_from_robots(base_url)
        sitemap_queue.extend(robots_sitemaps)
        
        # Add default sitemap paths
        for path in self.sitemap_paths:
            sitemap_queue.append(urljoin(base_url, path))
        
        # Process sitemap queue
        while sitemap_queue and len(all_urls) < 5000:
            sitemap_url = sitemap_queue.pop(0)
            
            if sitemap_url in processed_sitemaps:
                continue
            
            processed_sitemaps.add(sitemap_url)
            
            try:
                content = self._fetch_url(sitemap_url)
                if not content:
                    continue
                
                # Check if it's a sitemap index
                if '<sitemapindex' in content or '<sitemap>' in content:
                    child_sitemaps = self._extract_sitemap_urls(content)
                    for child in child_sitemaps:
                        if child not in processed_sitemaps:
                            sitemap_queue.append(child)
                
                # Extract page URLs
                urls = self._extract_page_urls(content, domain)
                all_urls.extend(urls)
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching sitemap {sitemap_url}: {e}")
                continue
        
        # Deduplicate
        seen = set()
        unique_urls = []
        for url_data in all_urls:
            if url_data['url'] not in seen:
                seen.add(url_data['url'])
                unique_urls.append(url_data)
        
        return unique_urls
    
    def _get_sitemaps_from_robots(self, base_url: str) -> List[str]:
        """Extract sitemap URLs from robots.txt"""
        try:
            response = self.session.get(
                f"{base_url}/robots.txt",
                timeout=10
            )
            
            if response.status_code == 200:
                sitemaps = re.findall(
                    r'Sitemap:\s*(.+)',
                    response.text,
                    re.IGNORECASE
                )
                return [s.strip() for s in sitemaps]
        except:
            pass
        
        return []
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None
    
    def _extract_sitemap_urls(self, content: str) -> List[str]:
        """Extract child sitemap URLs from sitemap index"""
        urls = []
        
        # Try regex first (faster)
        matches = re.findall(r'<loc>([^<]+)</loc>', content)
        for match in matches:
            if '.xml' in match.lower():
                urls.append(match.strip())
        
        return urls
    
    def _extract_page_urls(self, content: str, domain: str) -> List[Dict]:
        """Extract page URLs from sitemap"""
        urls = []
        
        # Extract all loc tags
        matches = re.findall(r'<loc>([^<]+)</loc>', content)
        
        for url in matches:
            url = url.strip()
            
            # Skip if it's another sitemap
            if '.xml' in url.lower():
                continue
            
            # Skip non-English URLs
            if not self._is_english_url(url):
                continue
            
            # Extract slug
            parsed = urlparse(url)
            slug = parsed.path.rstrip('/')
            
            urls.append({
                'url': url,
                'slug': slug,
                'domain': domain
            })
        
        return urls
    
    def _is_english_url(self, url: str) -> bool:
        """
        Check if URL appears to be English content
        Uses pattern matching for common non-English indicators
        """
        url_lower = url.lower()
        
        # Language path patterns to reject
        foreign_patterns = [
            '/pt/', '/br/', '/pt-br/', '/es/', '/de/', '/fr/', '/it/',
            '/nl/', '/ja/', '/jp/', '/ko/', '/kr/', '/zh/', '/cn/',
            '/ru/', '/ar/', '/pl/', '/tr/', '/sv/', '/da/', '/fi/',
            '/no/', '/cs/', '/hu/', '/ro/', '/uk/', '/el/', '/he/',
            '/vi/', '/th/', '/id/', '/ms/', '/hi/',
            '/blog-pt/', '/blog-es/', '/blog-de/', '/blog-fr/',
            '/recursos/', '/ressources/', '/ressourcen/', '/risorse/',
            'lang=pt', 'lang=es', 'lang=de', 'lang=fr',
            'locale=pt', 'locale=es', 'locale=de', 'locale=fr',
            '/hc/pt', '/hc/es', '/hc/de', '/hc/fr', '/hc/ja'
        ]
        
        for pattern in foreign_patterns:
            if pattern in url_lower:
                return False
        
        # Check for language codes in path segments
        path_parts = url_lower.split('/')
        language_codes = [
            'pt', 'br', 'es', 'de', 'fr', 'it', 'nl', 'ja', 'jp',
            'ko', 'kr', 'zh', 'cn', 'ru', 'ar', 'pl', 'tr', 'sv',
            'da', 'fi', 'no', 'cs', 'hu', 'ro', 'uk', 'el', 'he',
            'vi', 'th', 'id', 'ms', 'hi', 'ptbr'
        ]
        
        for part in path_parts:
            if part in language_codes:
                return False
            # Check for patterns like pt-br, es-mx
            if re.match(r'^[a-z]{2}-[a-z]{2}$', part) and part != 'en-us' and part != 'en-gb':
                return False
        
        return True
    
    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a page
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content or None
        """
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script, style, nav, footer elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # Try to find main content
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find(class_=re.compile(r'content|post|article|blog', re.I)) or
                soup.find('body')
            )
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                return text[:10000]  # Limit to 10k chars
            
            return None
            
        except Exception as e:
            print(f"Error fetching page content: {e}")
            return None
