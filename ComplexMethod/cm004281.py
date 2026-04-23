def register(
        config_class, tokenizer_class=None, slow_tokenizer_class=None, fast_tokenizer_class=None, exist_ok=False
    ):
        """
        Register a new tokenizer in this mapping.

        Args:
            config_class ([`PreTrainedConfig`]):
                The configuration corresponding to the model to register.
            tokenizer_class: The tokenizer class to register (V5 - preferred parameter).
            slow_tokenizer_class: (Deprecated) The slow tokenizer to register.
            fast_tokenizer_class: (Deprecated) The fast tokenizer to register.
        """
        if tokenizer_class is None:
            # Legacy: prefer fast over slow
            if fast_tokenizer_class is not None:
                tokenizer_class = fast_tokenizer_class
            elif slow_tokenizer_class is not None:
                tokenizer_class = slow_tokenizer_class
            else:
                raise ValueError("You need to pass a `tokenizer_class`")

        for candidate in (slow_tokenizer_class, fast_tokenizer_class, tokenizer_class):
            if candidate is not None:
                REGISTERED_TOKENIZER_CLASSES[candidate.__name__] = candidate

        if slow_tokenizer_class is not None and fast_tokenizer_class is not None:
            REGISTERED_FAST_ALIASES[slow_tokenizer_class.__name__] = fast_tokenizer_class

        TOKENIZER_MAPPING.register(config_class, tokenizer_class, exist_ok=exist_ok)