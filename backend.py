"""
SEO Blog Generator - Backend CLI
================================

Standalone command-line interface for running the blog generator
without the Streamlit frontend.

Usage:
    python backend.py --config config.json
    python backend.py --interactive

This can be used:
1. As a standalone script
2. Imported as a module in other Python applications
3. Called from APIs or other services
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from modules.sitemap_scraper import SitemapScraper
from modules.keyword_extractor import KeywordExtractor
from modules.content_analyzer import ContentAnalyzer
from modules.blog_generator import BlogGenerator
from modules.utils import export_to_json, export_to_csv


class SEOBlogGenerator:
    """
    Main class for SEO Blog Generation
    
    Can be used programmatically or via CLI
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the blog generator
        
        Args:
            api_key: Claude/Anthropic API key
        """
        self.api_key = api_key
        self.scraper = SitemapScraper(api_key)
        self.extractor = KeywordExtractor(api_key)
        self.analyzer = ContentAnalyzer(api_key)
        
        # Data storage
        self.my_company_name = ""
        self.my_company_domain = ""
        self.my_urls = []
        self.competitor_data = {}
        self.company_style = {}
        self.link_map = {}
        self.product_context = {}
        self.keywords = []
        self.selected_keywords = []
        self.generated_blogs = []
    
    def set_company_info(
        self,
        company_name: str,
        primary_domain: str,
        additional_domains: List[str] = None
    ):
        """
        Set your company information
        
        Args:
            company_name: Your company name
            primary_domain: Your main domain
            additional_domains: Additional domains/subdomains
        """
        self.my_company_name = company_name
        self.my_company_domain = primary_domain
        self.additional_domains = additional_domains or []
        
        print(f"✓ Company set: {company_name} ({primary_domain})")
    
    def fetch_my_sitemap(self) -> int:
        """
        Fetch your company's sitemap
        
        Returns:
            Number of URLs found
        """
        print(f"\n📥 Fetching sitemap for {self.my_company_domain}...")
        
        all_domains = [self.my_company_domain] + self.additional_domains
        self.my_urls = []
        
        for domain in all_domains:
            urls = self.scraper.fetch_sitemap(domain)
            self.my_urls.extend(urls)
            print(f"  • {domain}: {len(urls)} URLs")
        
        print(f"✓ Total: {len(self.my_urls)} URLs from your domain(s)")
        return len(self.my_urls)
    
    def learn_company_style(self):
        """Learn your company's writing style from existing content"""
        print("\n📖 Learning your content style...")
        
        self.company_style = self.analyzer.learn_company_style(self.my_urls[:50])
        print(f"✓ Style analysis complete")
        
        print("\n🔗 Building internal link map...")
        self.link_map = self.analyzer.build_link_map(self.my_urls)
        print(f"✓ Link map built with {len(self.link_map)} keywords")
        
        print("\n📦 Extracting product context...")
        self.product_context = self.analyzer.extract_product_context(self.my_urls)
        print(f"✓ Product context extracted")
    
    def add_competitors(self, competitor_names: List[str]) -> Dict[str, str]:
        """
        Add competitors and find their domains
        
        Args:
            competitor_names: List of competitor company names
            
        Returns:
            Dict mapping names to domains
        """
        print(f"\n🔍 Finding domains for {len(competitor_names)} competitors...")
        
        domains = self.scraper.find_domains(competitor_names)
        
        for name, domain in domains.items():
            print(f"  • {name}: {domain}")
        
        return domains
    
    def fetch_competitor_sitemaps(self, competitor_domains: Dict[str, str]) -> int:
        """
        Fetch sitemaps for all competitors
        
        Args:
            competitor_domains: Dict mapping names to domains
            
        Returns:
            Total URLs fetched
        """
        print(f"\n📥 Fetching competitor sitemaps...")
        
        self.competitor_data = {}
        total_urls = 0
        
        for name, domain in competitor_domains.items():
            print(f"  • Fetching {name} ({domain})...", end=" ")
            urls = self.scraper.fetch_sitemap(domain)
            
            self.competitor_data[name] = {
                'domain': domain,
                'urls': urls
            }
            
            total_urls += len(urls)
            print(f"{len(urls)} URLs")
        
        print(f"✓ Total: {total_urls} URLs from {len(competitor_domains)} competitors")
        return total_urls
    
    def extract_keywords(self, min_frequency: int = 2) -> List[Dict]:
        """
        Extract keywords and find gaps
        
        Args:
            min_frequency: Minimum keyword frequency
            
        Returns:
            List of keyword gap dicts
        """
        print(f"\n🔑 Extracting keywords from competitor URLs...")
        
        competitor_keywords = self.extractor.extract_from_urls(
            self.competitor_data,
            self.my_company_name
        )
        
        print(f"  • Found {len(competitor_keywords)} unique keywords from competitors")
        
        print("\n🏢 Extracting keywords from your URLs...")
        my_keywords = self.extractor.extract_from_url_list(self.my_urls, "my_company")
        print(f"  • Found {len(my_keywords)} keywords on your site")
        
        print("\n📊 Finding gaps...")
        self.keywords = self.extractor.find_gaps(
            competitor_keywords,
            my_keywords,
            min_frequency=min_frequency
        )
        
        print(f"✓ Found {len(self.keywords)} keyword gaps (competitors have, you don't)")
        
        return self.keywords
    
    def add_custom_keywords(self, keywords: List[str]):
        """
        Add custom keywords to the list
        
        Args:
            keywords: List of keyword strings
        """
        from datetime import datetime
        current_year = datetime.now().year
        
        for kw in keywords:
            kw = kw.strip()
            if kw and kw.lower() not in [k['keyword'].lower() for k in self.keywords]:
                self.keywords.append({
                    'keyword': kw,
                    'type': 'User Added',
                    'frequency': 0,
                    'competitor_count': 0,
                    'competitors': 'User Added',
                    'priority': 100,
                    'suggested_title': f"Complete Guide to {kw} ({current_year})"
                })
        
        print(f"✓ Added {len(keywords)} custom keywords")
    
    def select_keywords(self, indices: List[int] = None, count: int = None):
        """
        Select keywords for blog generation
        
        Args:
            indices: Specific indices to select
            count: Select top N keywords
        """
        if indices:
            self.selected_keywords = [self.keywords[i] for i in indices if i < len(self.keywords)]
        elif count:
            self.selected_keywords = self.keywords[:count]
        else:
            self.selected_keywords = self.keywords
        
        print(f"✓ Selected {len(self.selected_keywords)} keywords for blog generation")
    
    def generate_blogs(
        self,
        max_blogs: int = 10,
        include_internal_links: bool = True
    ) -> List[Dict]:
        """
        Generate blogs for selected keywords
        
        Args:
            max_blogs: Maximum number of blogs to generate
            include_internal_links: Whether to add internal links
            
        Returns:
            List of generated blog dicts
        """
        keywords_to_process = self.selected_keywords[:max_blogs]
        
        print(f"\n✨ Generating {len(keywords_to_process)} blogs...")
        
        generator = BlogGenerator(
            api_key=self.api_key,
            company_name=self.my_company_name,
            company_style=self.company_style,
            link_map=self.link_map,
            existing_urls=self.my_urls,
            product_context=self.product_context
        )
        
        self.generated_blogs = []
        
        for i, kw_data in enumerate(keywords_to_process):
            print(f"\n[{i+1}/{len(keywords_to_process)}] Generating: {kw_data['keyword']}")
            
            try:
                blog = generator.generate_blog(
                    keyword=kw_data['keyword'],
                    keyword_type=kw_data.get('type', 'Blog'),
                    competitors=kw_data.get('competitors', ''),
                    include_internal_links=include_internal_links
                )
                
                blog['keyword'] = kw_data['keyword']
                blog['type'] = kw_data.get('type', 'Blog')
                
                self.generated_blogs.append(blog)
                
                print(f"  ✓ {blog.get('title', 'Untitled')} ({blog.get('word_count', 0)} words)")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
        
        print(f"\n✅ Generated {len(self.generated_blogs)} blogs successfully!")
        
        return self.generated_blogs
    
    def export(self, output_dir: str = "output", formats: List[str] = None):
        """
        Export generated blogs
        
        Args:
            output_dir: Output directory
            formats: List of formats ('json', 'csv', 'markdown')
        """
        formats = formats or ['json', 'csv', 'markdown']
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if 'json' in formats:
            json_path = f"{output_dir}/blogs_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(export_to_json(self.generated_blogs))
            print(f"✓ Exported to {json_path}")
        
        if 'csv' in formats:
            csv_path = f"{output_dir}/blogs_{timestamp}.csv"
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(export_to_csv(self.generated_blogs))
            print(f"✓ Exported to {csv_path}")
        
        if 'markdown' in formats:
            md_dir = f"{output_dir}/markdown_{timestamp}"
            Path(md_dir).mkdir(parents=True, exist_ok=True)
            
            for blog in self.generated_blogs:
                # Create safe filename
                safe_title = "".join(c for c in blog.get('keyword', 'blog') if c.isalnum() or c in ' -_').strip()
                safe_title = safe_title.replace(' ', '_')[:50]
                
                md_path = f"{md_dir}/{safe_title}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {blog.get('title', '')}\n\n")
                    f.write(f"**Meta Description:** {blog.get('meta_description', '')}\n\n")
                    f.write(f"**Keyword:** {blog.get('keyword', '')}\n\n")
                    f.write(f"**Word Count:** {blog.get('word_count', 0)}\n\n")
                    f.write("---\n\n")
                    f.write(blog.get('content', ''))
            
            print(f"✓ Exported {len(self.generated_blogs)} markdown files to {md_dir}/")
    
    def get_keywords_for_review(self) -> List[Dict]:
        """Get keywords formatted for user review"""
        return [
            {
                'index': i,
                'keyword': kw['keyword'],
                'type': kw['type'],
                'frequency': kw['frequency'],
                'competitors': kw['competitors'],
                'priority': kw['priority'],
                'suggested_title': kw['suggested_title']
            }
            for i, kw in enumerate(self.keywords)
        ]
    
    def run_full_pipeline(
        self,
        company_name: str,
        company_domain: str,
        competitor_names: List[str],
        additional_keywords: List[str] = None,
        max_blogs: int = 10,
        output_dir: str = "output"
    ):
        """
        Run the complete pipeline
        
        Args:
            company_name: Your company name
            company_domain: Your domain
            competitor_names: List of competitor names
            additional_keywords: Extra keywords to target
            max_blogs: Maximum blogs to generate
            output_dir: Output directory for exports
        """
        print("=" * 60)
        print("SEO BLOG GENERATOR - FULL PIPELINE")
        print("=" * 60)
        
        # Step 1: Set company info
        self.set_company_info(company_name, company_domain)
        
        # Step 2: Fetch your sitemap
        self.fetch_my_sitemap()
        
        # Step 3: Learn your style
        self.learn_company_style()
        
        # Step 4: Add competitors
        competitor_domains = self.add_competitors(competitor_names)
        
        # Step 5: Fetch competitor sitemaps
        self.fetch_competitor_sitemaps(competitor_domains)
        
        # Step 6: Extract keywords
        self.extract_keywords()
        
        # Step 7: Add custom keywords
        if additional_keywords:
            self.add_custom_keywords(additional_keywords)
        
        # Step 8: Display keywords for review
        print("\n" + "=" * 60)
        print("KEYWORD REVIEW")
        print("=" * 60)
        print(f"\nTop {min(20, len(self.keywords))} keywords to target:\n")
        
        for i, kw in enumerate(self.keywords[:20]):
            print(f"{i+1:2}. {kw['keyword']}")
            print(f"    Type: {kw['type']} | Priority: {kw['priority']} | Competitors: {kw['competitor_count']}")
        
        # Step 9: Select top keywords
        self.select_keywords(count=max_blogs)
        
        # Step 10: Generate blogs
        self.generate_blogs(max_blogs=max_blogs)
        
        # Step 11: Export
        self.export(output_dir=output_dir)
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE!")
        print("=" * 60)


def interactive_mode(api_key: str):
    """Run in interactive mode with prompts"""
    generator = SEOBlogGenerator(api_key)
    
    print("\n" + "=" * 60)
    print("SEO BLOG GENERATOR - INTERACTIVE MODE")
    print("=" * 60)
    
    # Get company info
    print("\n📋 STEP 1: Your Company Information")
    company_name = input("  Company Name: ").strip()
    company_domain = input("  Primary Domain: ").strip()
    
    generator.set_company_info(company_name, company_domain)
    
    # Fetch sitemap
    print("\n📥 STEP 2: Fetching Your Sitemap")
    generator.fetch_my_sitemap()
    
    # Learn style
    print("\n📖 STEP 3: Learning Your Style")
    generator.learn_company_style()
    
    # Get competitors
    print("\n🎯 STEP 4: Competitors")
    print("  Enter competitor names (one per line, empty line to finish):")
    
    competitors = []
    while True:
        comp = input("  > ").strip()
        if not comp:
            break
        competitors.append(comp)
    
    if not competitors:
        print("  No competitors entered. Using default list.")
        competitors = ["Synthesia", "Scribe", "Loom"]
    
    # Fetch competitor data
    competitor_domains = generator.add_competitors(competitors)
    generator.fetch_competitor_sitemaps(competitor_domains)
    
    # Extract keywords
    print("\n🔑 STEP 5: Extracting Keywords")
    generator.extract_keywords()
    
    # Additional keywords
    print("\n➕ STEP 6: Additional Keywords")
    print("  Enter additional keywords to target (one per line, empty line to finish):")
    
    additional = []
    while True:
        kw = input("  > ").strip()
        if not kw:
            break
        additional.append(kw)
    
    if additional:
        generator.add_custom_keywords(additional)
    
    # Review keywords
    print("\n📋 STEP 7: Review Keywords")
    keywords = generator.get_keywords_for_review()
    
    print(f"\n  Found {len(keywords)} keyword gaps. Top 20:\n")
    for kw in keywords[:20]:
        print(f"  {kw['index']+1:2}. {kw['keyword']} (Priority: {kw['priority']})")
    
    # Select keywords
    print("\n  How many blogs to generate?")
    try:
        num_blogs = int(input("  Number (default 10): ").strip() or "10")
    except:
        num_blogs = 10
    
    generator.select_keywords(count=num_blogs)
    
    # Generate
    print("\n✨ STEP 8: Generating Blogs")
    confirm = input(f"  Generate {num_blogs} blogs? (y/n): ").strip().lower()
    
    if confirm == 'y':
        generator.generate_blogs(max_blogs=num_blogs)
        
        # Export
        print("\n📤 STEP 9: Export")
        output_dir = input("  Output directory (default 'output'): ").strip() or "output"
        generator.export(output_dir=output_dir)
    
    print("\n✅ Done!")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="SEO Blog Generator - Generate high-quality blogs from competitor analysis"
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='Claude API key (or set ANTHROPIC_API_KEY env var)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--company',
        type=str,
        help='Your company name'
    )
    
    parser.add_argument(
        '--domain',
        type=str,
        help='Your primary domain'
    )
    
    parser.add_argument(
        '--competitors',
        type=str,
        nargs='+',
        help='List of competitor names'
    )
    
    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        help='Additional keywords to target'
    )
    
    parser.add_argument(
        '--max-blogs',
        type=int,
        default=10,
        help='Maximum number of blogs to generate'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: Claude API key required")
        print("  Use --api-key or set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    # Run mode
    if args.interactive:
        interactive_mode(api_key)
    
    elif args.config:
        # Load config and run
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        generator = SEOBlogGenerator(api_key)
        generator.run_full_pipeline(
            company_name=config.get('company_name'),
            company_domain=config.get('company_domain'),
            competitor_names=config.get('competitors', []),
            additional_keywords=config.get('keywords', []),
            max_blogs=config.get('max_blogs', 10),
            output_dir=config.get('output_dir', 'output')
        )
    
    elif args.company and args.domain and args.competitors:
        # Run with CLI arguments
        generator = SEOBlogGenerator(api_key)
        generator.run_full_pipeline(
            company_name=args.company,
            company_domain=args.domain,
            competitor_names=args.competitors,
            additional_keywords=args.keywords or [],
            max_blogs=args.max_blogs,
            output_dir=args.output
        )
    
    else:
        # Show help
        parser.print_help()
        print("\n📖 Examples:")
        print("  # Interactive mode:")
        print("  python backend.py --api-key sk-ant-xxx --interactive")
        print("")
        print("  # With config file:")
        print("  python backend.py --api-key sk-ant-xxx --config config.json")
        print("")
        print("  # With CLI arguments:")
        print("  python backend.py --api-key sk-ant-xxx --company Trupeer --domain trupeer.ai --competitors Synthesia Loom Scribe")


if __name__ == "__main__":
    main()
