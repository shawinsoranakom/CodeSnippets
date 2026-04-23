def _calculate_url_relevance_score(self, query: str, url: str) -> float:
        """Calculate relevance score between query and URL using string matching."""
        # Normalize inputs
        query_lower = query.lower()
        url_lower = url.lower()

        # Extract URL components
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')

        # Create searchable text from URL
        # Split domain by dots and path by slashes
        domain_parts = domain.split('.')
        path_parts = [p for p in path.split('/') if p]

        # Include query parameters if any
        query_params = parsed.query
        param_parts = []
        if query_params:
            for param in query_params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    param_parts.extend([key, value])

        # Combine all parts
        all_parts = domain_parts + path_parts + param_parts

        # Calculate scores
        scores = []
        query_tokens = query_lower.split()

        # 1. Exact match in any part (highest score)
        for part in all_parts:
            part_lower = part.lower()
            if query_lower in part_lower:
                scores.append(1.0)
            elif part_lower in query_lower:
                scores.append(0.9)

        # 2. Token matching
        for token in query_tokens:
            token_scores = []
            for part in all_parts:
                part_lower = part.lower()
                if token in part_lower:
                    # Score based on how much of the part the token covers
                    coverage = len(token) / len(part_lower)
                    token_scores.append(0.7 * coverage)
                elif part_lower in token:
                    coverage = len(part_lower) / len(token)
                    token_scores.append(0.6 * coverage)

            if token_scores:
                scores.append(max(token_scores))

        # 3. Character n-gram similarity (for fuzzy matching)
        def get_ngrams(text, n=3):
            return set(text[i:i+n] for i in range(len(text)-n+1))

        # Combine all URL parts into one string for n-gram comparison
        url_text = ' '.join(all_parts).lower()
        if len(query_lower) >= 3 and len(url_text) >= 3:
            query_ngrams = get_ngrams(query_lower)
            url_ngrams = get_ngrams(url_text)
            if query_ngrams and url_ngrams:
                intersection = len(query_ngrams & url_ngrams)
                union = len(query_ngrams | url_ngrams)
                jaccard = intersection / union if union > 0 else 0
                scores.append(0.5 * jaccard)

        # Calculate final score
        if not scores:
            return 0.0

        # Weighted average with bias towards higher scores
        scores.sort(reverse=True)
        weighted_score = 0
        total_weight = 0
        for i, score in enumerate(scores):
            weight = 1 / (i + 1)  # Higher weight for better matches
            weighted_score += score * weight
            total_weight += weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0
        return min(final_score, 1.0)