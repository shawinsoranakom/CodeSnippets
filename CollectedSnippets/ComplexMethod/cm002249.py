def _topk_jaccard(
        self,
        query_tokens: set[str],
        identifiers: list[str],
        tokens_map: dict[str, list[str]],
        self_model_normalized: str,
        self_name: str,
        k: int,
    ) -> list[tuple[str, float]]:
        """
        Find top-k most similar definitions using Jaccard similarity on token sets.

        Args:
            query_tokens (`set[str]`): Set of tokens from the query definition.
            identifiers (`list[str]`): List of all definition identifiers in the index.
            tokens_map (`dict[str, list[str]]`): Mapping of identifiers to their token lists.
            self_model_normalized (`str`): Normalized name of the query model to exclude.
            self_name (`str`): Name of the query definition to exclude.
            k (`int`): Number of top results to return.

        Returns:
            `list[tuple[str, float]]`: List of (identifier, score) tuples.
        """
        scores = []
        for identifier in identifiers:
            parent_relative_path, match_name = identifier.split(":", 1)
            parent_model = Path(parent_relative_path).parts[0]
            if match_name == self_name:
                continue
            if self_model_normalized and _normalize(parent_model) == self_model_normalized:
                continue
            tokens = set(tokens_map.get(identifier, []))
            if not tokens or not query_tokens:
                continue
            score = len(query_tokens & tokens) / len(query_tokens | tokens)
            if score > 0:
                scores.append((identifier, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]