def __setattr__(self, key, value):
        # Handle _id/_ids suffix (eg. bos_token_id -> bos_token)
        key_without_id = key.removesuffix("_ids").removesuffix("_id") if key.endswith(("_id", "_ids")) else key

        # Named special tokens (bos_token, eos_token, etc.)
        if key_without_id in self.SPECIAL_TOKENS_ATTRIBUTES:
            if key != key_without_id and value is not None:
                value = self.convert_ids_to_tokens(value)
            if value is not None and not isinstance(value, (str, AddedToken)):
                raise ValueError(f"Cannot set a non-string value as the {key_without_id}")
            self._special_tokens_map[key_without_id] = value
            return

        # Extra special tokens: model-specific special tokens without standard names (eg. <mask_1>)
        if key_without_id == "extra_special_tokens":
            if key != key_without_id and value is not None and isinstance(value, (list, tuple)):
                value = [self.convert_ids_to_tokens(v) for v in value]
            if not isinstance(value, (list, tuple)) and value is not None:
                raise ValueError(f"extra_special_tokens must be a list or tuple, got {type(value)}")
            self._extra_special_tokens = [] if value is None else list(value)
            return

        super().__setattr__(key, value)