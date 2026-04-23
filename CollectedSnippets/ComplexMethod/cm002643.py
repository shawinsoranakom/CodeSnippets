def truncate_sequences(
        self,
        ids: list[int],
        pair_ids: list[int] | None = None,
        num_tokens_to_remove: int = 0,
        truncation_strategy: str | TruncationStrategy = "longest_first",
        stride: int = 0,
    ) -> tuple[list[int], list[int], list[int]]:
        """Truncates sequences according to the specified strategy."""
        if num_tokens_to_remove <= 0:
            return ids, pair_ids, []

        if not isinstance(truncation_strategy, TruncationStrategy):
            truncation_strategy = TruncationStrategy(truncation_strategy)

        overflowing_tokens = []

        # ONLY_FIRST or LONGEST_FIRST with single sequence
        if truncation_strategy == TruncationStrategy.ONLY_FIRST or (
            truncation_strategy == TruncationStrategy.LONGEST_FIRST and pair_ids is None
        ):
            window_len = min(len(ids), stride + num_tokens_to_remove)
            if self.truncation_side == "left":
                overflowing_tokens = ids[:window_len]
                ids = ids[num_tokens_to_remove:]
            else:
                overflowing_tokens = ids[-window_len:]
                ids = ids[:-num_tokens_to_remove]

        # LONGEST_FIRST with pair
        elif truncation_strategy == TruncationStrategy.LONGEST_FIRST:
            logger.warning(
                "Be aware, overflowing tokens are not returned for the setting you have chosen,"
                f" i.e. sequence pairs with the '{TruncationStrategy.LONGEST_FIRST.value}' "
                "truncation strategy. So the returned list will always be empty even if some "
                "tokens have been removed."
            )
            len_ids, len_pair = len(ids), len(pair_ids) if pair_ids else 0
            first_remove = min(abs(len_pair - len_ids), num_tokens_to_remove)
            second_remove = num_tokens_to_remove - first_remove

            if len_ids > len_pair:
                ids_to_move = first_remove + second_remove // 2
                pair_ids_to_move = second_remove - second_remove // 2
            else:
                ids_to_move = second_remove // 2
                pair_ids_to_move = first_remove + second_remove - (second_remove // 2)

            if self.truncation_side == "right":
                ids = ids[:-ids_to_move] if ids_to_move > 0 else ids
                pair_ids = pair_ids[:-pair_ids_to_move] if pair_ids and pair_ids_to_move > 0 else pair_ids
            else:
                ids = ids[ids_to_move:]
                pair_ids = pair_ids[pair_ids_to_move:] if pair_ids else None

        # ONLY_SECOND
        elif truncation_strategy == TruncationStrategy.ONLY_SECOND and pair_ids:
            window_len = min(len(pair_ids), stride + num_tokens_to_remove)
            if self.truncation_side == "right":
                overflowing_tokens = pair_ids[-window_len:]
                pair_ids = pair_ids[:-num_tokens_to_remove]
            else:
                overflowing_tokens = pair_ids[:window_len]
                pair_ids = pair_ids[num_tokens_to_remove:]

        return ids, pair_ids, overflowing_tokens