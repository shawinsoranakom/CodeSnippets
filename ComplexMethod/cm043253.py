def _calculate_novelty(self, link: Link, state: CrawlState) -> float:
        """Estimate how much new information this link might provide"""
        if not state.knowledge_base:
            return 1.0  # First links are maximally novel

        # Get terms from link preview
        link_text = ' '.join(filter(None, [
            link.text or '',
            link.title or '',
            link.head_data.get('title', '') if link.head_data else '',
            link.head_data.get('description', '') if link.head_data else '',
            link.head_data.get('keywords', '') if link.head_data else ''
        ])).lower()

        link_terms = set(self._tokenize(link_text))
        if not link_terms:
            return 0.5  # Unknown novelty

        # Calculate what percentage of link terms are new
        existing_terms = set(state.term_frequencies.keys())
        new_terms = link_terms - existing_terms

        novelty = len(new_terms) / len(link_terms) if link_terms else 0.0

        return novelty