def gather_pre_entities(
        self,
        sentence: str,
        input_ids: np.ndarray,
        scores: np.ndarray,
        offset_mapping: list[tuple[int, int]] | None,
        special_tokens_mask: np.ndarray,
        aggregation_strategy: AggregationStrategy,
        word_ids: list[int | None] | None = None,
        word_to_chars_map: list[tuple[int, int]] | None = None,
    ) -> list[dict]:
        """Fuse various numpy arrays into dicts with all the information needed for aggregation"""
        pre_entities = []
        for idx, token_scores in enumerate(scores):
            # Filter special_tokens
            if special_tokens_mask[idx]:
                continue

            word = self.tokenizer.convert_ids_to_tokens(int(input_ids[idx]))
            if offset_mapping is not None:
                start_ind, end_ind = offset_mapping[idx]

                # If the input is pre-tokenized, we need to rescale the offsets to the absolute sentence.
                if word_ids is not None and word_to_chars_map is not None:
                    word_index = word_ids[idx]
                    if word_index is not None:
                        start_char, _ = word_to_chars_map[word_index]
                        start_ind += start_char
                        end_ind += start_char

                if not isinstance(start_ind, int):
                    start_ind = start_ind.item()
                    end_ind = end_ind.item()
                word_ref = sentence[start_ind:end_ind]
                if getattr(self.tokenizer, "_tokenizer", None) and getattr(
                    self.tokenizer._tokenizer.model, "continuing_subword_prefix", None
                ):
                    # This is a BPE, word aware tokenizer, there is a correct way
                    # to fuse tokens
                    is_subword = len(word) != len(word_ref)
                else:
                    # This is a fallback heuristic. This will fail most likely on any kind of text + punctuation mixtures that will be considered "words". Non word aware models cannot do better than this unfortunately.
                    if aggregation_strategy in {
                        AggregationStrategy.FIRST,
                        AggregationStrategy.AVERAGE,
                        AggregationStrategy.MAX,
                    }:
                        warnings.warn(
                            "Tokenizer does not support real words, using fallback heuristic",
                            UserWarning,
                        )
                    is_subword = start_ind > 0 and " " not in sentence[start_ind - 1 : start_ind + 1]

                if int(input_ids[idx]) == self.tokenizer.unk_token_id:
                    word = word_ref
                    is_subword = False
            else:
                start_ind = None
                end_ind = None
                is_subword = False

            pre_entity = {
                "word": word,
                "scores": token_scores,
                "start": start_ind,
                "end": end_ind,
                "index": idx,
                "is_subword": is_subword,
            }
            pre_entities.append(pre_entity)
        return pre_entities