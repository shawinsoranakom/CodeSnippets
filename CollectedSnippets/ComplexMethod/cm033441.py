def extract_language(self, content: ScrapedContent) -> str:
        """Extract language from content metadata."""
        if content.metadata and content.metadata.get("language"):
            return content.metadata["language"]

        # Simple language detection based on common words
        if content.markdown:
            text = content.markdown.lower()
            if any(word in text for word in ["the", "and", "or", "but", "in", "on", "at"]):
                return "en"
            elif any(word in text for word in ["le", "la", "les", "de", "du", "des"]):
                return "fr"
            elif any(word in text for word in ["der", "die", "das", "und", "oder"]):
                return "de"
            elif any(word in text for word in ["el", "la", "los", "las", "de", "del"]):
                return "es"

        return "en"