def _calculate_relevance(self, link: Link, state: CrawlState) -> float:
        """BM25 relevance score between link preview and query"""
        if not state.query or not link:
            return 0.0

        # Combine available text from link
        link_text = ' '.join(filter(None, [
            link.text or '',
            link.title or '',
            link.head_data.get('meta', {}).get('title', '') if link.head_data else '',
            link.head_data.get('meta', {}).get('description', '') if link.head_data else '',
            link.head_data.get('meta', {}).get('keywords', '') if link.head_data else ''
        ])).lower()

        if not link_text:
            return 0.0

        # Use contextual score if available (from BM25 scoring during crawl)
        # if link.contextual_score is not None:
        if link.contextual_score and link.contextual_score > 0:
            return link.contextual_score

        # Otherwise, calculate simple term overlap
        query_terms = set(self._tokenize(state.query.lower()))
        link_terms = set(self._tokenize(link_text))

        if not query_terms:
            return 0.0

        overlap = len(query_terms & link_terms) / len(query_terms)
        return overlap