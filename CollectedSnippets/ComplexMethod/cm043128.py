def calculate_academic_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score for academic content"""
        score = 0.0
        content_lower = content.lower()

        # Check for academic keywords
        keyword_matches = sum(1 for kw in self.academic_keywords if kw in content_lower)
        score += keyword_matches * 0.1

        # Check for citations
        citation_count = sum(
            len(re.findall(pattern, content)) 
            for pattern in self.citation_patterns
        )
        score += min(citation_count * 0.05, 1.0)  # Cap at 1.0

        # Check for query terms in academic context
        query_terms = query.lower().split()
        for term in query_terms:
            # Boost if term appears near academic keywords
            for keyword in ['abstract', 'conclusion', 'results']:
                if keyword in content_lower:
                    section = content_lower[content_lower.find(keyword):content_lower.find(keyword) + 500]
                    if term in section:
                        score += 0.2

        return min(score, 2.0)