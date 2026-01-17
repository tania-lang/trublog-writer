"""
Blog Generator Module
=====================

Handles:
- Generating high-quality blog content
- Applying company style
- Adding internal links
- Updating dates/years
- Quality guardrails
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
import anthropic


class BlogGenerator:
    """AI-powered blog content generator with quality guardrails"""
    
    def __init__(
        self,
        api_key: str,
        company_name: str,
        company_style: Dict = None,
        link_map: Dict = None,
        existing_urls: List[Dict] = None,
        product_context: Dict = None
    ):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.company_name = company_name
        self.company_style = company_style or {}
        self.link_map = link_map or {}
        self.existing_urls = existing_urls or []
        self.product_context = product_context or {}
        self.current_year = datetime.now().year
    
    def generate_blog(
        self,
        keyword: str,
        keyword_type: str = "Blog",
        competitors: str = "",
        include_internal_links: bool = True
    ) -> Dict:
        """
        Generate a complete blog post
        
        Args:
            keyword: Target keyword
            keyword_type: Type of content (Blog, Tool, Solution, etc.)
            competitors: Competitors covering this topic
            include_internal_links: Whether to add internal links
            
        Returns:
            Dict with title, content, meta_description, word_count
        """
        # Build the comprehensive prompt
        prompt = self._build_generation_prompt(
            keyword=keyword,
            keyword_type=keyword_type,
            competitors=competitors,
            include_internal_links=include_internal_links
        )
        
        # Generate with Claude
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Parse the response
            blog = self._parse_blog_response(response_text, keyword)
            
            # Post-process
            blog['content'] = self._post_process_content(blog['content'])
            
            # Add internal links if requested
            if include_internal_links:
                blog['content'] = self._add_internal_links(blog['content'])
            
            # Calculate word count
            blog['word_count'] = len(blog['content'].split())
            
            # Validate quality
            if blog['word_count'] < 2000:
                # Try to expand
                blog = self._expand_blog(blog, keyword)
            
            return blog
            
        except Exception as e:
            print(f"Error generating blog: {e}")
            return {
                'title': f"{keyword} - Complete Guide",
                'content': f"Error generating content: {str(e)}",
                'meta_description': f"Learn about {keyword}",
                'word_count': 0
            }
    
    def _build_generation_prompt(
        self,
        keyword: str,
        keyword_type: str,
        competitors: str,
        include_internal_links: bool
    ) -> str:
        """Build the comprehensive blog generation prompt"""
        
        # Style instructions
        style_instructions = self._get_style_instructions()
        
        # Product context
        product_info = self._get_product_context()
        
        # Internal linking context
        link_context = self._get_link_context(keyword) if include_internal_links else ""
        
        prompt = f"""You are a senior content writer for {self.company_name}. Write a comprehensive, high-quality blog post.

=== TARGET KEYWORD ===
Keyword: {keyword}
Content Type: {keyword_type}
Competitors covering this: {competitors}

=== COMPANY CONTEXT ===
Company: {self.company_name}
{product_info}

=== WRITING STYLE (Follow Exactly) ===
{style_instructions}

=== INTERNAL LINKING OPPORTUNITIES ===
{link_context}

=== CRITICAL REQUIREMENTS ===

1. LENGTH: Minimum 2500 words. Each section must be detailed and substantive. Do not write thin content.

2. LANGUAGE: 
   - Write in American English only
   - All spellings must be correct
   - Use American spellings (color not colour, optimize not optimise)

3. DATES AND YEARS:
   - Current year is {self.current_year}
   - Use {self.current_year} for all "this year" references
   - Never use 2024, 2023, or older years as current
   - Update any outdated statistics to reflect {self.current_year}

4. COMPANY NAME INTEGRATION:
   - When the topic allows, naturally mention {self.company_name}
   - Replace generic "[company]" placeholders with {self.company_name}
   - Add {self.company_name} as a solution where relevant

5. NO AI MARKERS (Critical - will make content detectable as AI):
   - Never use em dashes (—) or en dashes (–). Use commas or periods instead.
   - Never use these phrases:
     * "In today's world/digital age/fast-paced environment"
     * "In this article/blog post/comprehensive guide"
     * "Let's dive in/explore/delve into"
     * "It's worth noting/important to note"
     * "When it comes to"
     * "At the end of the day"
     * "First and foremost" / "Last but not least"
     * "In conclusion" / "To summarize"
     * "Moving forward" / "Going forward"
   - Never use these words:
     * leverage, utilize, optimal, streamline, robust
     * cutting-edge, game-changer, paradigm shift, synergy
     * holistic, revolutionize, empower, delve, realm
     * landscape, tapestry, multifaceted, myriad, plethora
     * moreover, furthermore, additionally, consequently
     * nevertheless, nonetheless, henceforth, thereby

6. HUMAN WRITING STYLE:
   - Use contractions naturally (don't, can't, won't, it's, you'll, we've)
   - Vary sentence length (some short. Some medium. And occasionally longer ones.)
   - Start some sentences with But, And, So, Now, Sometimes
   - Include personal perspective ("From experience", "What works well is")
   - Be direct and practical, not fluffy
   - Use "you" and "your" to address the reader

7. STRUCTURE:
   
   # [Compelling Title with Keyword - include {self.current_year} if appropriate]
   
   [Introduction: 3-4 paragraphs, 250+ words. Start with a specific problem or scenario. NO generic openings.]
   
   ## [Section 1: Clear statement header - NOT a question]
   [300+ words with specific details, examples, and actionable advice]
   
   ### [Subsection if needed]
   [Detailed explanation]
   
   [Continue for 6-8 main H2 sections, each with substantial content]
   
   ## Comparison Table (where relevant)
   | Feature | Option A | Option B | Option C |
   |---------|----------|----------|----------|
   | Specific detail | Value | Value | Value |
   
   ## Key Takeaways
   [Practical summary - don't say "in conclusion"]
   
   ## Frequently Asked Questions
   
   **Q: Specific question 1?**
   A: Direct answer in 2-3 sentences.
   
   [5 FAQs total]

8. INTERNAL LINKS:
   - Add 3-5 internal links to relevant {self.company_name} pages
   - Use natural anchor text
   - Format: [anchor text](URL)
   - Only link to URLs provided in the linking context

9. QUALITY GUARDRAILS:
   - Every paragraph must have substance (no filler)
   - Include specific numbers, statistics, and examples
   - Make every claim actionable
   - No repetitive phrases or sentences
   - Vary paragraph lengths

=== OUTPUT FORMAT ===
Return your response in this exact format:

TITLE: [Your compelling title here]

META_DESCRIPTION: [150-160 character SEO meta description]

CONTENT:
[Full blog content in Markdown format, minimum 2500 words]

---

Write the blog now. Remember: minimum 2500 words, no AI markers, natural human style."""

        return prompt
    
    def _get_style_instructions(self) -> str:
        """Get style instructions from company style analysis"""
        if not self.company_style:
            return """
- Tone: Professional but approachable
- Voice: Second person (you/your)
- Paragraphs: Medium length (3-5 sentences)
- Use clear H2/H3 headers
- Moderate use of bullets and bold
- Natural, contextual internal links"""
        
        instructions = []
        
        if self.company_style.get('tone'):
            instructions.append(f"- Tone: {self.company_style['tone']}")
        
        if self.company_style.get('voice'):
            instructions.append(f"- Voice: {self.company_style['voice']}")
        
        if self.company_style.get('paragraph_length'):
            instructions.append(f"- Paragraphs: {self.company_style['paragraph_length']}")
        
        if self.company_style.get('use_of_headers'):
            instructions.append(f"- Headers: {self.company_style['use_of_headers']}")
        
        if self.company_style.get('formatting_style'):
            instructions.append(f"- Formatting: {self.company_style['formatting_style']}")
        
        if self.company_style.get('unique_phrases'):
            phrases = self.company_style['unique_phrases'][:5]
            if phrases:
                instructions.append(f"- Use phrases like: {', '.join(phrases)}")
        
        if self.company_style.get('cta_style'):
            instructions.append(f"- CTAs: {self.company_style['cta_style']}")
        
        return '\n'.join(instructions) if instructions else "- Use professional, approachable tone"
    
    def _get_product_context(self) -> str:
        """Get product context for the prompt"""
        if not self.product_context:
            return f"Product: {self.company_name} (no additional context available)"
        
        context_parts = []
        
        if self.product_context.get('product_description'):
            context_parts.append(f"Product Description: {self.product_context['product_description']}")
        
        if self.product_context.get('key_features'):
            features = self.product_context['key_features'][:5]
            context_parts.append(f"Key Features: {', '.join(features)}")
        
        if self.product_context.get('use_cases'):
            use_cases = self.product_context['use_cases'][:5]
            context_parts.append(f"Use Cases: {', '.join(use_cases)}")
        
        if self.product_context.get('target_audience'):
            context_parts.append(f"Target Audience: {self.product_context['target_audience']}")
        
        if self.product_context.get('value_propositions'):
            props = self.product_context['value_propositions'][:3]
            context_parts.append(f"Value Props: {', '.join(props)}")
        
        return '\n'.join(context_parts) if context_parts else ""
    
    def _get_link_context(self, keyword: str) -> str:
        """Get relevant internal links for the keyword"""
        if not self.link_map:
            return "No internal links available"
        
        relevant_links = []
        keyword_lower = keyword.lower()
        keyword_words = set(keyword_lower.split())
        
        # Find relevant links
        for link_keyword, links in self.link_map.items():
            link_words = set(link_keyword.lower().split())
            
            # Check for overlap
            if keyword_words & link_words or keyword_lower in link_keyword or link_keyword in keyword_lower:
                for link in links[:2]:  # Max 2 per keyword
                    relevant_links.append(f"- {link['anchor_text']}: {link['url']}")
        
        # Also add some general links
        for link_keyword, links in list(self.link_map.items())[:10]:
            for link in links[:1]:
                link_text = f"- {link['anchor_text']}: {link['url']}"
                if link_text not in relevant_links:
                    relevant_links.append(link_text)
        
        if relevant_links:
            return "Available pages to link to:\n" + '\n'.join(relevant_links[:15])
        
        return "No internal links available"
    
    def _parse_blog_response(self, response: str, keyword: str) -> Dict:
        """Parse the blog response into structured format"""
        result = {
            'title': f"{keyword} - Complete Guide {self.current_year}",
            'meta_description': f"Learn about {keyword} with this comprehensive guide.",
            'content': response
        }
        
        # Try to extract title
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|META)', response, re.IGNORECASE | re.DOTALL)
        if title_match:
            result['title'] = title_match.group(1).strip()
        
        # Try to extract meta description
        meta_match = re.search(r'META_DESCRIPTION:\s*(.+?)(?:\n|CONTENT)', response, re.IGNORECASE | re.DOTALL)
        if meta_match:
            result['meta_description'] = meta_match.group(1).strip()[:160]
        
        # Try to extract content
        content_match = re.search(r'CONTENT:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        if content_match:
            result['content'] = content_match.group(1).strip()
        
        return result
    
    def _post_process_content(self, content: str) -> str:
        """Clean up and improve generated content"""
        if not content:
            return content
        
        # Replace dashes with commas
        content = re.sub(r'\s*[—–]\s*', ', ', content)
        content = re.sub(r'\s+-\s+', ', ', content)
        
        # Update years
        old_years = ['2024', '2023', '2022', '2021', '2020']
        for old_year in old_years:
            # Only replace when used as "current" year
            content = re.sub(
                rf'\b{old_year}\b(?!\s*[-–])',  # Don't replace in date ranges
                str(self.current_year),
                content
            )
        
        # Remove AI-sounding phrases
        ai_phrases = [
            r"in today's (?:world|digital age|fast-paced)",
            r"in this (?:article|blog post|comprehensive guide)",
            r"let's (?:dive in|explore|delve)",
            r"it's (?:worth noting|important to note)",
            r"when it comes to",
            r"at the end of the day",
            r"first and foremost",
            r"last but not least",
            r"without further ado",
            r"as we(?:'ve)? (?:discussed|mentioned|seen)",
            r"moving forward",
            r"going forward",
        ]
        
        for phrase in ai_phrases:
            content = re.sub(phrase, '', content, flags=re.IGNORECASE)
        
        # Clean up double spaces and commas
        content = re.sub(r',\s*,', ',', content)
        content = re.sub(r'\s{2,}', ' ', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Fix any broken sentences from removals
        content = re.sub(r'\.\s+,', '.', content)
        content = re.sub(r',\s+\.', '.', content)
        
        return content.strip()
    
    def _add_internal_links(self, content: str) -> str:
        """Add internal links to the content"""
        if not self.link_map:
            return content
        
        links_added = 0
        max_links = 5
        
        for link_keyword, links in self.link_map.items():
            if links_added >= max_links:
                break
            
            # Check if keyword appears in content
            pattern = re.compile(re.escape(link_keyword), re.IGNORECASE)
            
            if pattern.search(content):
                # Only replace first occurrence
                link = links[0]
                replacement = f"[{link_keyword}]({link['url']})"
                
                content = pattern.sub(replacement, content, count=1)
                links_added += 1
        
        return content
    
    def _expand_blog(self, blog: Dict, keyword: str) -> Dict:
        """Expand a blog that's too short"""
        prompt = f"""The following blog about "{keyword}" is too short ({blog['word_count']} words). 
Expand it to at least 2500 words by adding more detail, examples, and sections.

Current content:
{blog['content'][:5000]}

Add:
1. More detailed explanations in each section
2. Additional examples and use cases
3. More subsections with H3 headers
4. Expanded FAQ section
5. More practical tips and actionable advice

Return the expanded content in Markdown format. Maintain the same style and tone.
Do not use AI-sounding phrases or dashes."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            expanded_content = response.content[0].text
            expanded_content = self._post_process_content(expanded_content)
            
            blog['content'] = expanded_content
            blog['word_count'] = len(expanded_content.split())
            
        except Exception as e:
            print(f"Error expanding blog: {e}")
        
        return blog
    
    def spell_check(self, content: str) -> str:
        """Use Claude to spell check content"""
        prompt = f"""Fix any spelling errors in this content. 

RULES:
- Only fix obvious spelling mistakes
- Use American English spellings
- Do not change grammar, style, or formatting
- Do not add or remove content
- Return the corrected content only

CONTENT:
{content[:12000]}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error spell checking: {e}")
            return content
