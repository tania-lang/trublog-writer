# SEO Blog Generator

A comprehensive AI-powered SEO blog generation tool that analyzes competitor content, learns your writing style, and generates high-quality blog posts targeting keyword gaps.

## Features

- **Competitor Analysis**: Automatically finds competitor domains and scrapes their sitemaps
- **Keyword Gap Detection**: Identifies keywords competitors rank for that you don't
- **Style Learning**: Learns your company's writing style from existing content
- **Internal Linking**: Automatically adds relevant internal links to generated content
- **Product Context**: Extracts and uses your product information in blogs
- **Quality Guardrails**: Ensures content is high-quality, properly spelled, and doesn't sound AI-generated
- **Multiple Interfaces**: Use via Streamlit web UI, CLI, or as a Python module

## Requirements

- Python 3.9+
- Claude API key (Anthropic)

## Installation

1. Clone or download this repository:
```bash
cd seo_blog_generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Or create a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

### Option 1: Streamlit Web Interface (Recommended)

```bash
streamlit run app.py
```

This opens a web interface where you can:
1. Enter your company and competitor information
2. Fetch and analyze sitemaps
3. Review and select keywords
4. Generate blogs
5. Export in multiple formats

### Option 2: Command Line Interface

**Interactive Mode:**
```bash
python backend.py --api-key sk-ant-xxx --interactive
```

**With Config File:**
```bash
python backend.py --api-key sk-ant-xxx --config config.json
```

**With CLI Arguments:**
```bash
python backend.py \
  --api-key sk-ant-xxx \
  --company "Trupeer" \
  --domain "trupeer.ai" \
  --competitors Synthesia Loom Scribe Vidyard \
  --keywords "AI video generator" "training video software" \
  --max-blogs 10 \
  --output ./output
```

### Option 3: Python Module

```python
from backend import SEOBlogGenerator

# Initialize
generator = SEOBlogGenerator(api_key="sk-ant-xxx")

# Set company info
generator.set_company_info("Trupeer", "trupeer.ai")

# Fetch your sitemap
generator.fetch_my_sitemap()

# Learn your style
generator.learn_company_style()

# Add and analyze competitors
competitor_domains = generator.add_competitors([
    "Synthesia", "Loom", "Scribe"
])
generator.fetch_competitor_sitemaps(competitor_domains)

# Extract keywords
keywords = generator.extract_keywords(min_frequency=2)

# Add custom keywords
generator.add_custom_keywords(["AI video generator", "training videos"])

# Review keywords
for kw in generator.get_keywords_for_review()[:10]:
    print(f"{kw['keyword']} - Priority: {kw['priority']}")

# Select and generate
generator.select_keywords(count=10)
blogs = generator.generate_blogs(max_blogs=10)

# Export
generator.export(output_dir="output", formats=["json", "csv", "markdown"])
```

## Configuration

Create a `config.json` file (see `config.example.json`):

```json
{
  "company_name": "Your Company",
  "company_domain": "yourcompany.com",
  "competitors": ["Competitor1", "Competitor2"],
  "keywords": ["additional keyword 1", "additional keyword 2"],
  "max_blogs": 10,
  "min_frequency": 2,
  "output_dir": "output"
}
```

## Output Formats

### JSON
```json
{
  "generated_at": "2025-01-17T...",
  "blogs": [
    {
      "keyword": "AI Video Generator",
      "title": "Best AI Video Generators in 2025",
      "meta_description": "...",
      "content": "...",
      "word_count": 2750
    }
  ]
}
```

### CSV
| Keyword | Title | Meta Description | Content | Word Count |
|---------|-------|------------------|---------|------------|
| ... | ... | ... | ... | ... |

### Markdown
Individual `.md` files for each blog post.

## API Needed

### Required: Claude API (Anthropic)

Get your API key from: https://console.anthropic.com/

The tool uses Claude for:
- Finding competitor domains from company names
- Extracting meaningful keywords from URLs
- Analyzing your writing style
- Generating blog content
- Spell checking

**Pricing Note**: Claude API is pay-per-use. Generating 10 blogs typically costs $1-3 depending on content length.

## How It Works

### Step 1: Sitemap Fetching
- Finds competitor domains using Claude
- Fetches sitemap.xml from all domains
- Extracts all English URLs

### Step 2: Keyword Extraction
- Analyzes URL slugs to extract keywords
- Uses AI to validate keywords are meaningful English phrases
- Filters out non-content pages (login, pricing, etc.)

### Step 3: Gap Analysis
- Compares competitor keywords to your keywords
- Calculates priority: `(Frequency × 3) + (CompetitorCount × 5) + Score`
- Ranks gaps by priority

### Step 4: Style Learning
- Fetches sample content from your site
- Analyzes tone, voice, formatting patterns
- Builds internal link map

### Step 5: Blog Generation
- Generates 2500+ word blogs
- Applies your writing style
- Adds internal links
- Updates dates/years
- Removes AI-sounding phrases

## Quality Guardrails

The generator includes multiple guardrails:

### Language
- English-only filtering for URLs and keywords
- American English spelling
- Spell checking pass

### Content Quality
- Minimum 2500 words
- No thin paragraphs
- Specific examples and statistics
- Varied sentence structure

### Anti-AI Detection
- No dashes (em/en dash)
- No AI phrases ("In today's world", "Let's dive in", etc.)
- No corporate buzzwords (leverage, synergy, etc.)
- Natural contractions
- Human writing patterns

### SEO
- Keyword in title
- Meta description
- Proper header structure (H1, H2, H3)
- Internal linking
- Current year references

## Troubleshooting

### "API key not found"
Set your API key via environment variable or `--api-key` flag.

### "No URLs found"
The domain might not have a sitemap.xml or it's blocked. Check manually.

### "Keywords look wrong"
The AI extracts from URL slugs. If competitor URLs are poorly structured, keywords may be low quality. Add custom keywords manually.

### "Blog too short"
The generator will automatically try to expand short blogs. If it still fails, the API might be rate limited. Wait and try again.

## Project Structure

```
seo_blog_generator/
├── app.py                 # Streamlit web interface
├── backend.py             # CLI and Python module
├── requirements.txt       # Python dependencies
├── config.example.json    # Sample configuration
├── README.md              # This file
└── modules/
    ├── __init__.py
    ├── sitemap_scraper.py # Sitemap fetching
    ├── keyword_extractor.py # Keyword extraction
    ├── content_analyzer.py  # Style learning
    ├── blog_generator.py    # Blog generation
    └── utils.py             # Utilities
```

## License

MIT License - Use freely for personal or commercial projects.

## Support

For issues or questions, please open a GitHub issue.
