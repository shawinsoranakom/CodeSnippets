def _calculate_coverage(self, state: CrawlState) -> float:
        """Coverage scoring - measures query term presence across knowledge base

        Returns a score between 0 and 1, where:
        - 0 means no query terms found
        - 1 means excellent coverage of all query terms
        """
        if not state.query or state.total_documents == 0:
            return 0.0

        query_terms = self._tokenize(state.query.lower())
        if not query_terms:
            return 0.0

        term_scores = []
        max_tf = max(state.term_frequencies.values()) if state.term_frequencies else 1

        for term in query_terms:
            tf = state.term_frequencies.get(term, 0)
            df = state.document_frequencies.get(term, 0)

            if df > 0:
                # Document coverage: what fraction of docs contain this term
                doc_coverage = df / state.total_documents

                # Frequency signal: normalized log frequency  
                freq_signal = math.log(1 + tf) / math.log(1 + max_tf) if max_tf > 0 else 0

                # Combined score: document coverage with frequency boost
                term_score = doc_coverage * (1 + 0.5 * freq_signal)
                term_scores.append(term_score)
            else:
                term_scores.append(0.0)

        # Average across all query terms
        coverage = sum(term_scores) / len(term_scores)

        # Apply square root curve to make score more intuitive
        # This helps differentiate between partial and good coverage
        return min(1.0, math.sqrt(coverage))