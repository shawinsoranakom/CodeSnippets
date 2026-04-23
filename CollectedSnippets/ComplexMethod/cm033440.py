def extract_description(self, content: ScrapedContent) -> str:
        """Extract description from scraped content."""
        if content.description:
            return content.description

        if content.metadata and content.metadata.get("description"):
            return content.metadata["description"]

        # Extract first paragraph from markdown
        if content.markdown:
            # Remove headers and get first paragraph
            text = re.sub(r'^#+\s+.*$', '', content.markdown, flags=re.MULTILINE)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if paragraphs:
                return paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]

        return ""