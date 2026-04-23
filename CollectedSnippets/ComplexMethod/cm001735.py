def extract(self) -> tuple[dict[str, int], list[tuple[str, float]], list[tuple[str, str]], list[dict]]:
        """
        Extract vocabulary, scores, merges, and added_tokens from the tokenizer.json file.

        Returns:
            tuple containing:
                - vocab_ids (dict[str, int]): Mapping from token string to token ID
                - vocab_scores (list[tuple[str, float]]): List of (token, score) tuples.
                  Note: tokenizer.json doesn't store scores, so all scores are 0.0
                - merges (list[tuple[str, str]]): List of merge pairs for BPE tokenizers
                - added_tokens (list[dict]): List of added token dicts with 'id', 'content', 'special', etc.

        Raises:
            ValueError: If the tokenizer type is not supported or vocab is missing
        """
        # Extract vocabulary
        if "vocab" not in self.model_data:
            raise ValueError(f"Tokenizer model type '{self.model_type}' does not have a 'vocab' field")

        vocab_field = self.model_data["vocab"]

        # Support both dict-based (BPE/WordPiece/WordLevel) and list-based (Unigram) vocabs
        if isinstance(vocab_field, dict):
            # {token: id}
            vocab_ids = dict(vocab_field)
            # tokenizer.json doesn't store scores for these types; default to 0.0 and sort by id
            vocab_scores = sorted([(token, 0.0) for token in vocab_field.keys()], key=lambda x: vocab_field[x[0]])
        elif isinstance(vocab_field, list):
            # [[token, score], ...] — ids are the list indices
            vocab_ids = {token: idx for idx, (token, _score) in enumerate(vocab_field)}
            vocab_scores = [(token, float(score)) for token, score in vocab_field]
        else:
            raise ValueError(f"Unsupported vocab type in tokenizer.json: {type(vocab_field)}")

        # Extract merges (for BPE tokenizers)
        merges = []
        if "merges" in self.model_data:
            # tokenizer.json can store merges as either:
            # 1. Lists like ["▁", "t"]
            # 2. Strings like "▁ t"
            for merge_item in self.model_data["merges"]:
                if isinstance(merge_item, list):
                    # Already in list format
                    if len(merge_item) == 2:
                        merges.append((merge_item[0], merge_item[1]))
                    else:
                        logger.warning(f"Invalid merge format (expected 2 items): {merge_item}, skipping")
                elif isinstance(merge_item, str):
                    # String format - split on first space
                    parts = merge_item.split(" ", 1)
                    if len(parts) == 2:
                        merges.append((parts[0], parts[1]))
                    else:
                        logger.warning(f"Invalid merge format: '{merge_item}', skipping")
                else:
                    logger.warning(f"Unknown merge type: {type(merge_item)}, skipping")

        # Extract added_tokens from tokenizer.json
        # These are tokens that should not be split by the tokenization algorithm
        added_tokens_list = self.tokenizer_data.get("added_tokens", [])
        # Convert to decoder-style mapping: id -> token dict
        added_tokens_decoder = {}
        for item in added_tokens_list:
            if not isinstance(item, dict) or "id" not in item:
                continue
            token_id = item["id"]
            token_kwargs = {k: v for k, v in item.items() if k != "id"}
            try:
                added_token_obj = AddedToken(**token_kwargs)
            except Exception:
                # Fallback: at minimum require content
                content = token_kwargs.get("content")
                if content is None:
                    continue
                added_token_obj = AddedToken(content, special=bool(token_kwargs.get("special", True)))
            added_tokens_decoder[token_id] = added_token_obj

        return vocab_ids, vocab_scores, merges, added_tokens_decoder