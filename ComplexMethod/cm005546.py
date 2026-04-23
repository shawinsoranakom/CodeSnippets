def cleanup(cls):
        """
        Clean up dead references in the cache.
        This removes entries where either the target_tokenizer or assistant_tokenizer
        has been garbage collected.
        """
        # Remove entries from the outer cache where the target_tokenizer is no longer alive
        dead_keys = [key for key in cls._cache if key is None]
        for key in dead_keys:
            del cls._cache[key]

        # For each assistant_dict, remove entries where assistant_tokenizer is no longer alive
        for assistant_dict in cls._cache.values():
            dead_keys = [key for key in assistant_dict if key is None]
            for key in dead_keys:
                del assistant_dict[key]