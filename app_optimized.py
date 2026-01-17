"""
SEO Blog Generator - Cost-Optimized Streamlit App
=================================================

Run with: streamlit run app_optimized.py

Cost savings:
- Uses Haiku ($0.25/1M) for simple tasks vs Sonnet ($3/1M)
- Local keyword extraction (no API)
- Caching to avoid repeat calls
- Estimated: $0.50-1.00 for 10 blogs (vs $2-3 before)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time
from pathlib import Path

from cost_optimized import (
    CostOptimizedBlogGenerator,
    OptimizedAPIClient,
    LocalKeywordExtractor
)

# Page config
st.set_page_config(
    page_title="SEO Blog Generator (Cost Optimized)",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .cost-badge {
        background: #4caf50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    .savings-box {
        background: #e8f5e9;
        border: 1px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'generator' not in st.session_state:
    st.session_state.generator = None
if 'keywords' not in st.session_state:
    st.session_state.keywords = []
if 'selected_keywords' not in st.session_state:
    st.session_state.selected_keywords = []
if 'generated_blogs' not in st.session_state:
    st.session_state.generated_blogs = []


def main():
    st.title("💰 SEO Blog Generator (Cost Optimized)")
    
    st.markdown("""
    <div class="savings-box">
    <strong>💡 Cost Optimization Active:</strong><br>
    • Uses Claude Haiku for simple tasks (10x cheaper)<br>
    • Local keyword extraction (no API cost)<br>
    • Results caching (no repeat charges)<br>
    • <strong>Estimated: $0.50-1.00 for 10 blogs</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ API Key")
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.api_key,
            help="Get from console.anthropic.com"
        )
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API Key set")
        else:
            st.warning("⚠️ Enter API key")
        
        st.divider()
        
        # Cost tracker
        if st.session_state.generator:
            st.metric(
                "💰 Current Cost",
                f"${st.session_state.generator.api.total_cost:.4f}"
            )
            st.caption(f"API Calls: {st.session_state.generator.api.call_count}")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Setup",
        "2️⃣ Keywords", 
        "3️⃣ Generate",
        "4️⃣ Export"
    ])
    
    # TAB 1: SETUP
    with tab1:
        st.header("📋 Company Setup")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Your Company")
            company_name = st.text_input("Company Name", placeholder="e.g., Trupeer")
            company_domain = st.text_input("Domain", placeholder="e.g., trupeer.ai")
        
        with col2:
            st.subheader("Competitors")
            competitors = st.text_area(
                "Competitor Names (one per line)",
                placeholder="Synthesia\nLoom\nScribe",
                height=150
            )
        
        if st.button("🚀 Start Analysis", type="primary"):
            if not st.session_state.api_key:
                st.error("Enter API key first")
                return
            
            if not company_name or not company_domain or not competitors:
                st.error("Fill all fields")
                return
            
            comp_list = [c.strip() for c in competitors.split('\n') if c.strip()]
            
            with st.spinner("Analyzing (this is the cheap part)..."):
                # Initialize generator
                gen = CostOptimizedBlogGenerator(st.session_state.api_key)
                
                # Setup
                st.write("📥 Fetching your sitemap...")
                gen.setup(company_name, company_domain)
                st.write(f"   ✓ Found {len(gen.my_urls)} URLs")
                
                # Competitors
                st.write("🔍 Analyzing competitors...")
                gen.add_competitors(comp_list)
                
                for name, data in gen.competitor_data.items():
                    st.write(f"   ✓ {name}: {len(data['urls'])} URLs")
                
                # Keywords
                st.write("🔑 Extracting keywords (local, free)...")
                keywords = gen.extract_keywords()
                
                st.session_state.generator = gen
                st.session_state.keywords = keywords
                
                st.success(f"✅ Found {len(keywords)} keyword gaps!")
                st.info(f"💰 Cost so far: ${gen.api.total_cost:.4f}")
    
    # TAB 2: KEYWORDS
    with tab2:
        st.header("🔑 Keyword Selection")
        
        if not st.session_state.keywords:
            st.warning("Complete Step 1 first")
            return
        
        st.write(f"Found **{len(st.session_state.keywords)}** keyword gaps")
        
        # Add custom keywords
        custom = st.text_area("➕ Add Custom Keywords (optional)", height=80)
        if st.button("Add Custom"):
            for kw in custom.split('\n'):
                kw = kw.strip()
                if kw:
                    st.session_state.keywords.insert(0, {
                        'keyword': kw,
                        'type': 'Custom',
                        'frequency': 0,
                        'competitor_count': 0,
                        'competitors': 'User Added',
                        'priority': 999
                    })
            st.rerun()
        
        # Keyword table
        df = pd.DataFrame(st.session_state.keywords[:100])
        df.insert(0, 'Select', False)
        
        edited = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn("✓", default=False),
                "keyword": "Keyword",
                "type": "Type",
                "frequency": "Freq",
                "competitor_count": "Comps",
                "priority": "Priority"
            },
            hide_index=True,
            use_container_width=True
        )
        
        selected = edited[edited['Select'] == True].to_dict('records')
        st.session_state.selected_keywords = selected
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Select Top 5"):
                st.session_state.selected_keywords = st.session_state.keywords[:5]
                st.rerun()
        with col2:
            if st.button("Select Top 10"):
                st.session_state.selected_keywords = st.session_state.keywords[:10]
                st.rerun()
        with col3:
            if st.button("Select Top 20"):
                st.session_state.selected_keywords = st.session_state.keywords[:20]
                st.rerun()
        with col4:
            st.write(f"**Selected: {len(st.session_state.selected_keywords)}**")
    
    # TAB 3: GENERATE
    with tab3:
        st.header("✨ Generate Blogs")
        
        if not st.session_state.selected_keywords:
            st.warning("Select keywords in Step 2 first")
            return
        
        st.write(f"**{len(st.session_state.selected_keywords)} keywords selected**")
        
        # Cost estimate
        estimated_cost = len(st.session_state.selected_keywords) * 0.08
        st.info(f"💰 Estimated cost: ${estimated_cost:.2f} (using Sonnet for generation only)")
        
        num_blogs = st.selectbox("Blogs to generate", [5, 10, 20, 50], index=1)
        
        if st.button("🚀 Generate Blogs", type="primary"):
            gen = st.session_state.generator
            
            if not gen:
                st.error("Run setup first")
                return
            
            progress = st.progress(0)
            status = st.empty()
            
            keywords_to_gen = st.session_state.selected_keywords[:num_blogs]
            
            blogs = []
            for i, kw in enumerate(keywords_to_gen):
                status.text(f"Generating: {kw['keyword']}...")
                
                try:
                    from cost_optimized import OptimizedBlogGenerator
                    
                    blog_gen = OptimizedBlogGenerator(
                        api_client=gen.api,
                        company_name=gen.my_company_name,
                        company_style=gen.company_style,
                        link_map=gen.link_map
                    )
                    
                    blog = blog_gen.generate_blog(kw['keyword'], kw.get('type', 'Blog'))
                    blog['keyword'] = kw['keyword']
                    blog['type'] = kw.get('type', 'Blog')
                    blogs.append(blog)
                    
                    st.success(f"✓ {blog['title']} ({blog['word_count']} words)")
                    
                except Exception as e:
                    st.error(f"✗ {kw['keyword']}: {e}")
                
                progress.progress((i + 1) / len(keywords_to_gen))
                time.sleep(1)
            
            st.session_state.generated_blogs = blogs
            status.text("✅ Complete!")
            
            st.info(f"💰 Total cost: ${gen.api.total_cost:.4f}")
        
        # Show generated blogs
        if st.session_state.generated_blogs:
            st.subheader("📄 Generated Blogs")
            
            for blog in st.session_state.generated_blogs:
                with st.expander(f"📝 {blog.get('title', blog['keyword'])}"):
                    st.write(f"**Words:** {blog.get('word_count', 0)}")
                    st.write(f"**Meta:** {blog.get('meta_description', '')}")
                    st.markdown(blog.get('content', '')[:2000] + "...")
    
    # TAB 4: EXPORT
    with tab4:
        st.header("📤 Export")
        
        if not st.session_state.generated_blogs:
            st.warning("Generate blogs first")
            return
        
        st.write(f"**{len(st.session_state.generated_blogs)} blogs ready**")
        
        # Cost summary
        if st.session_state.generator:
            st.success(f"💰 Final cost: ${st.session_state.generator.api.total_cost:.4f}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON export
            json_data = json.dumps({
                'generated_at': datetime.now().isoformat(),
                'blogs': st.session_state.generated_blogs
            }, indent=2)
            
            st.download_button(
                "📥 Download JSON",
                json_data,
                f"blogs_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json"
            )
        
        with col2:
            # CSV export
            csv_rows = []
            for blog in st.session_state.generated_blogs:
                csv_rows.append({
                    'Keyword': blog['keyword'],
                    'Title': blog.get('title', ''),
                    'Meta': blog.get('meta_description', ''),
                    'Words': blog.get('word_count', 0),
                    'Content': blog.get('content', '')
                })
            
            df = pd.DataFrame(csv_rows)
            
            st.download_button(
                "📥 Download CSV",
                df.to_csv(index=False),
                f"blogs_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        
        # Preview
        st.subheader("Preview")
        preview_df = pd.DataFrame([
            {
                'Title': b.get('title', ''),
                'Keyword': b['keyword'],
                'Words': b.get('word_count', 0)
            }
            for b in st.session_state.generated_blogs
        ])
        st.dataframe(preview_df, use_container_width=True)


if __name__ == "__main__":
    main()
