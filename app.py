"""
SEO Blog Generator - Main Application
======================================

A comprehensive SEO blog generation tool with:
- Intelligent competitor analysis
- AI-powered keyword extraction
- Style learning from your existing content
- High-quality blog generation

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time

# Import our modules
from modules.sitemap_scraper import SitemapScraper
from modules.keyword_extractor import KeywordExtractor
from modules.content_analyzer import ContentAnalyzer
from modules.blog_generator import BlogGenerator
from modules.utils import init_session_state, export_to_csv, export_to_json

# Page config
st.set_page_config(
    page_title="SEO Blog Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(90deg, #1a73e8, #4285f4);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .keyword-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .priority-high {
        background: #d4edda;
        border-color: #28a745;
    }
    .priority-medium {
        background: #fff3cd;
        border-color: #ffc107;
    }
    .gap-indicator {
        background: #f8d7da;
        color: #721c24;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background: #e7f3ff;
        border: 1px solid #1a73e8;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()


def main():
    """Main application entry point"""
    
    # Header
    st.markdown('<p class="main-header">📝 SEO Blog Generator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered blog generation with competitor analysis and style learning</p>', unsafe_allow_html=True)
    
    # Sidebar - API Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Your Anthropic Claude API key (starts with sk-ant-)"
        )
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ Enter your Claude API key to continue")
        
        st.divider()
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            st.session_state.min_word_count = st.number_input(
                "Minimum blog word count",
                min_value=1000,
                max_value=5000,
                value=2500,
                step=500
            )
            
            st.session_state.min_competitor_frequency = st.number_input(
                "Minimum keyword frequency",
                min_value=1,
                max_value=10,
                value=2,
                help="Keyword must appear in at least this many competitor pages"
            )
            
            st.session_state.max_blogs = st.number_input(
                "Maximum blogs to generate",
                min_value=1,
                max_value=100,
                value=10
            )
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1️⃣ Setup",
        "2️⃣ Analysis",
        "3️⃣ Keywords",
        "4️⃣ Generate",
        "5️⃣ Export"
    ])
    
    # ============================================
    # TAB 1: SETUP
    # ============================================
    with tab1:
        st.markdown('<div class="step-header">📋 Step 1: Enter Company Information</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Your Company")
            
            my_company_name = st.text_input(
                "Company Name",
                value=st.session_state.get('my_company_name', ''),
                placeholder="e.g., Trupeer",
                help="Your company name for style learning"
            )
            
            my_company_domain = st.text_input(
                "Primary Domain",
                value=st.session_state.get('my_company_domain', ''),
                placeholder="e.g., trupeer.ai",
                help="Your main website domain"
            )
            
            my_additional_domains = st.text_area(
                "Additional Domains/Subdomains (one per line)",
                value=st.session_state.get('my_additional_domains', ''),
                placeholder="blog.trupeer.ai\ndocs.trupeer.ai",
                height=100
            )
        
        with col2:
            st.subheader("Competitors")
            
            competitor_names = st.text_area(
                "Competitor Names (one per line)",
                value=st.session_state.get('competitor_names', ''),
                placeholder="Synthesia\nScribe\nGuidde\nVidyard\nLoom",
                height=150,
                help="Enter competitor company names. We'll find their domains automatically."
            )
            
            additional_keywords = st.text_area(
                "Additional Keywords to Target (optional)",
                value=st.session_state.get('additional_keywords', ''),
                placeholder="AI video generator\nScreen recording software\nDocumentation tools",
                height=100,
                help="Additional keywords you want to target beyond competitor analysis"
            )
        
        # Save to session state
        if st.button("💾 Save Configuration", type="primary"):
            st.session_state.my_company_name = my_company_name
            st.session_state.my_company_domain = my_company_domain
            st.session_state.my_additional_domains = my_additional_domains
            st.session_state.competitor_names = competitor_names
            st.session_state.additional_keywords = additional_keywords
            st.success("✅ Configuration saved! Proceed to Analysis tab.")
    
    # ============================================
    # TAB 2: ANALYSIS
    # ============================================
    with tab2:
        st.markdown('<div class="step-header">🔍 Step 2: Fetch & Analyze Sitemaps</div>', unsafe_allow_html=True)
        
        if not st.session_state.get('api_key'):
            st.error("⚠️ Please enter your Claude API key in the sidebar first.")
            return
        
        if not st.session_state.get('my_company_domain'):
            st.warning("⚠️ Please complete Step 1 (Setup) first.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Your Company Analysis")
            
            if st.button("🔄 Fetch My Company Sitemap", type="primary"):
                with st.spinner("Fetching your sitemap and analyzing content..."):
                    scraper = SitemapScraper(st.session_state.api_key)
                    
                    # Fetch sitemap
                    my_domains = [st.session_state.my_company_domain]
                    if st.session_state.get('my_additional_domains'):
                        my_domains.extend([d.strip() for d in st.session_state.my_additional_domains.split('\n') if d.strip()])
                    
                    my_urls = []
                    for domain in my_domains:
                        urls = scraper.fetch_sitemap(domain)
                        my_urls.extend(urls)
                        st.write(f"✅ {domain}: {len(urls)} URLs")
                    
                    st.session_state.my_urls = my_urls
                    
                    # Analyze content
                    analyzer = ContentAnalyzer(st.session_state.api_key)
                    
                    st.write("📖 Learning your content style...")
                    style_analysis = analyzer.learn_company_style(my_urls[:50])  # Analyze first 50 pages
                    st.session_state.company_style = style_analysis
                    
                    st.write("🔗 Building internal link map...")
                    link_map = analyzer.build_link_map(my_urls)
                    st.session_state.link_map = link_map
                    
                    st.success(f"✅ Analyzed {len(my_urls)} URLs from your domain")
            
            if st.session_state.get('my_urls'):
                st.metric("Your URLs", len(st.session_state.my_urls))
                
                if st.session_state.get('company_style'):
                    with st.expander("📊 Your Writing Style Analysis"):
                        st.json(st.session_state.company_style)
        
        with col2:
            st.subheader("🎯 Competitor Analysis")
            
            if st.button("🔄 Fetch Competitor Sitemaps", type="primary"):
                if not st.session_state.get('competitor_names'):
                    st.error("Please enter competitor names in Step 1")
                    return
                
                with st.spinner("Finding competitor domains and fetching sitemaps..."):
                    scraper = SitemapScraper(st.session_state.api_key)
                    
                    competitors = [c.strip() for c in st.session_state.competitor_names.split('\n') if c.strip()]
                    
                    # Find domains using Claude
                    st.write("🔍 Finding competitor domains...")
                    competitor_domains = scraper.find_domains(competitors)
                    st.session_state.competitor_domains = competitor_domains
                    
                    # Fetch sitemaps
                    all_competitor_urls = {}
                    progress = st.progress(0)
                    
                    for i, (name, domain) in enumerate(competitor_domains.items()):
                        st.write(f"📥 Fetching {name} ({domain})...")
                        urls = scraper.fetch_sitemap(domain)
                        all_competitor_urls[name] = {
                            'domain': domain,
                            'urls': urls
                        }
                        progress.progress((i + 1) / len(competitor_domains))
                        time.sleep(1)  # Rate limiting
                    
                    st.session_state.competitor_urls = all_competitor_urls
                    
                    total_urls = sum(len(c['urls']) for c in all_competitor_urls.values())
                    st.success(f"✅ Fetched {total_urls} URLs from {len(competitor_domains)} competitors")
            
            if st.session_state.get('competitor_urls'):
                st.write("**Competitor URL Counts:**")
                for name, data in st.session_state.competitor_urls.items():
                    st.write(f"• {name}: {len(data['urls'])} URLs")
    
    # ============================================
    # TAB 3: KEYWORDS
    # ============================================
    with tab3:
        st.markdown('<div class="step-header">🔑 Step 3: Keyword Analysis & Gap Detection</div>', unsafe_allow_html=True)
        
        if not st.session_state.get('competitor_urls'):
            st.warning("⚠️ Please complete Step 2 (Analysis) first.")
            return
        
        if st.button("🔍 Extract & Analyze Keywords", type="primary"):
            with st.spinner("Extracting keywords and finding gaps..."):
                extractor = KeywordExtractor(st.session_state.api_key)
                
                # Extract keywords from competitors
                st.write("🔑 Extracting keywords from competitor URLs...")
                competitor_keywords = extractor.extract_from_urls(
                    st.session_state.competitor_urls,
                    st.session_state.my_company_name
                )
                
                # Extract keywords from my company
                st.write("🏢 Extracting keywords from your URLs...")
                my_keywords = extractor.extract_from_url_list(
                    st.session_state.my_urls,
                    "my_company"
                )
                
                # Find gaps
                st.write("📊 Analyzing gaps...")
                gap_analysis = extractor.find_gaps(
                    competitor_keywords,
                    my_keywords,
                    min_frequency=st.session_state.get('min_competitor_frequency', 2)
                )
                
                # Add additional keywords from user
                if st.session_state.get('additional_keywords'):
                    additional = [k.strip() for k in st.session_state.additional_keywords.split('\n') if k.strip()]
                    for kw in additional:
                        if kw.lower() not in [g['keyword'].lower() for g in gap_analysis]:
                            gap_analysis.append({
                                'keyword': kw,
                                'type': 'User Added',
                                'frequency': 0,
                                'competitor_count': 0,
                                'competitors': 'User Added',
                                'priority': 100,
                                'suggested_title': f"Complete Guide to {kw}"
                            })
                
                st.session_state.gap_analysis = gap_analysis
                st.session_state.competitor_keywords = competitor_keywords
                st.session_state.my_keywords = my_keywords
                
                st.success(f"✅ Found {len(gap_analysis)} keyword gaps!")
        
        # Display keywords for review
        if st.session_state.get('gap_analysis'):
            st.subheader("📋 Review & Select Keywords")
            
            st.markdown("""
            <div class="info-box">
            <strong>Priority Formula:</strong> (Frequency × 3) + (Competitor Count × 5) + Base Score<br>
            <strong>Gap:</strong> Keywords your competitors have that you don't
            </div>
            """, unsafe_allow_html=True)
            
            # Add user keywords input
            new_keywords = st.text_area(
                "➕ Add More Keywords (one per line)",
                placeholder="Enter additional keywords you want to target...",
                height=100
            )
            
            if st.button("Add Keywords"):
                if new_keywords:
                    for kw in new_keywords.split('\n'):
                        kw = kw.strip()
                        if kw and kw.lower() not in [g['keyword'].lower() for g in st.session_state.gap_analysis]:
                            st.session_state.gap_analysis.append({
                                'keyword': kw,
                                'type': 'User Added',
                                'frequency': 0,
                                'competitor_count': 0,
                                'competitors': 'User Added',
                                'priority': 100,
                                'suggested_title': f"Complete Guide to {kw}"
                            })
                    st.success("✅ Keywords added!")
                    st.rerun()
            
            # Create dataframe for selection
            df = pd.DataFrame(st.session_state.gap_analysis)
            df = df.sort_values('priority', ascending=False)
            
            # Add selection column
            df.insert(0, 'Select', True)
            
            # Display editable dataframe
            edited_df = st.data_editor(
                df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select keywords to generate blogs for",
                        default=True
                    ),
                    "keyword": st.column_config.TextColumn("Keyword", width="medium"),
                    "type": st.column_config.TextColumn("Type", width="small"),
                    "frequency": st.column_config.NumberColumn("Frequency", width="small"),
                    "competitor_count": st.column_config.NumberColumn("Competitors", width="small"),
                    "priority": st.column_config.NumberColumn("Priority", width="small"),
                    "suggested_title": st.column_config.TextColumn("Suggested Title", width="large"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Save selected keywords
            selected = edited_df[edited_df['Select'] == True]
            st.session_state.selected_keywords = selected.to_dict('records')
            
            st.write(f"**Selected: {len(st.session_state.selected_keywords)} keywords**")
            
            # Quick selection buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Select Top 5"):
                    st.session_state.selected_keywords = df.head(5).to_dict('records')
                    st.rerun()
            with col2:
                if st.button("Select Top 10"):
                    st.session_state.selected_keywords = df.head(10).to_dict('records')
                    st.rerun()
            with col3:
                if st.button("Select Top 20"):
                    st.session_state.selected_keywords = df.head(20).to_dict('records')
                    st.rerun()
            with col4:
                if st.button("Select All"):
                    st.session_state.selected_keywords = df.to_dict('records')
                    st.rerun()
    
    # ============================================
    # TAB 4: GENERATE BLOGS
    # ============================================
    with tab4:
        st.markdown('<div class="step-header">✨ Step 4: Generate Blogs</div>', unsafe_allow_html=True)
        
        if not st.session_state.get('selected_keywords'):
            st.warning("⚠️ Please select keywords in Step 3 first.")
            return
        
        st.write(f"**Ready to generate {len(st.session_state.selected_keywords)} blogs**")
        
        # Generation options
        col1, col2 = st.columns(2)
        
        with col1:
            num_blogs = st.selectbox(
                "Number of blogs to generate",
                options=[5, 10, 20, 50],
                index=1
            )
        
        with col2:
            include_internal_links = st.checkbox(
                "Include internal links",
                value=True,
                help="Add links to your existing pages where relevant"
            )
        
        if st.button("🚀 Generate Blogs", type="primary"):
            if not st.session_state.get('api_key'):
                st.error("Please enter your Claude API key")
                return
            
            keywords_to_process = st.session_state.selected_keywords[:num_blogs]
            
            generator = BlogGenerator(
                api_key=st.session_state.api_key,
                company_name=st.session_state.my_company_name,
                company_style=st.session_state.get('company_style', {}),
                link_map=st.session_state.get('link_map', {}),
                existing_urls=st.session_state.get('my_urls', [])
            )
            
            generated_blogs = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, kw_data in enumerate(keywords_to_process):
                status_text.text(f"Generating blog {i+1}/{len(keywords_to_process)}: {kw_data['keyword']}")
                
                try:
                    blog = generator.generate_blog(
                        keyword=kw_data['keyword'],
                        keyword_type=kw_data.get('type', 'Blog'),
                        competitors=kw_data.get('competitors', ''),
                        include_internal_links=include_internal_links
                    )
                    
                    generated_blogs.append({
                        'keyword': kw_data['keyword'],
                        'type': kw_data.get('type', 'Blog'),
                        **blog
                    })
                    
                    st.success(f"✅ Generated: {blog.get('title', kw_data['keyword'])}")
                    
                except Exception as e:
                    st.error(f"❌ Failed to generate blog for '{kw_data['keyword']}': {str(e)}")
                
                progress_bar.progress((i + 1) / len(keywords_to_process))
                time.sleep(2)  # Rate limiting
            
            st.session_state.generated_blogs = generated_blogs
            status_text.text("✅ Generation complete!")
            
            st.success(f"🎉 Successfully generated {len(generated_blogs)} blogs!")
        
        # Display generated blogs
        if st.session_state.get('generated_blogs'):
            st.subheader("📄 Generated Blogs")
            
            for i, blog in enumerate(st.session_state.generated_blogs):
                with st.expander(f"📝 {blog.get('title', blog['keyword'])}", expanded=False):
                    st.write(f"**Keyword:** {blog['keyword']}")
                    st.write(f"**Type:** {blog['type']}")
                    st.write(f"**Word Count:** {blog.get('word_count', 'N/A')}")
                    st.write(f"**Meta Description:** {blog.get('meta_description', 'N/A')}")
                    
                    st.divider()
                    
                    st.markdown("**Preview:**")
                    st.markdown(blog.get('content', '')[:2000] + "..." if len(blog.get('content', '')) > 2000 else blog.get('content', ''))
    
    # ============================================
    # TAB 5: EXPORT
    # ============================================
    with tab5:
        st.markdown('<div class="step-header">📤 Step 5: Export Blogs</div>', unsafe_allow_html=True)
        
        if not st.session_state.get('generated_blogs'):
            st.warning("⚠️ Please generate blogs in Step 4 first.")
            return
        
        st.write(f"**{len(st.session_state.generated_blogs)} blogs ready for export**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export as JSON
            json_data = export_to_json(st.session_state.generated_blogs)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Export as CSV
            csv_data = export_to_csv(st.session_state.generated_blogs)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col3:
            # Export individual markdown files info
            st.info("💡 Each blog can also be copied individually from the Generate tab")
        
        # Preview table
        st.subheader("📊 Export Preview")
        
        preview_data = []
        for blog in st.session_state.generated_blogs:
            preview_data.append({
                'Title': blog.get('title', ''),
                'Keyword': blog['keyword'],
                'Type': blog['type'],
                'Word Count': blog.get('word_count', 0),
                'Meta Description': blog.get('meta_description', '')[:100] + '...'
            })
        
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)


if __name__ == "__main__":
    main()
