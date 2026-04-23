def _sanity_check(fast_tokenizer, slow_tokenizer, keep_fast_tokenizer=False):
        """Set tokenizer(s) to `None` if the fast/slow tokenizers have different values for `vocab_size` or `length`.

        If `keep_fast_tokenizer=True`, the fast tokenizer will be kept.
        """
        # sanity check 1: fast and slow tokenizers should be compatible (vocab_size)
        if fast_tokenizer is not None and slow_tokenizer is not None:
            if fast_tokenizer.vocab_size != slow_tokenizer.vocab_size:
                warning_message = (
                    "The fast/slow tokenizers "
                    f"({fast_tokenizer.__class__.__name__}/{slow_tokenizer.__class__.__name__}) have different "
                    "vocabulary size: "
                    f"fast_tokenizer.vocab_size = {fast_tokenizer.vocab_size} and "
                    f"slow_tokenizer.vocab_size = {slow_tokenizer.vocab_size}."
                )
                result["warnings"].append(warning_message)
                if not keep_fast_tokenizer:
                    fast_tokenizer = None
                slow_tokenizer = None

        # sanity check 2: fast and slow tokenizers should be compatible (length)
        if fast_tokenizer is not None and slow_tokenizer is not None:
            if len(fast_tokenizer) != len(slow_tokenizer):
                warning_message = (
                    f"The fast/slow tokenizers () have different length: "
                    f"len(fast_tokenizer) = {len(fast_tokenizer)} and "
                    f"len(slow_tokenizer) = {len(slow_tokenizer)}."
                )
                result["warnings"].append(warning_message)
                if not keep_fast_tokenizer:
                    fast_tokenizer = None
                slow_tokenizer = None

        return fast_tokenizer, slow_tokenizer