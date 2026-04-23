def __getattr__(self, key):
        # Handle _id/_ids suffix (eg. bos_token_id -> bos_token)
        key_without_id = key.removesuffix("_ids").removesuffix("_id") if key.endswith(("_id", "_ids")) else key

        # Named special tokens (bos_token, eos_token, etc.)
        if key_without_id in self.SPECIAL_TOKENS_ATTRIBUTES:
            # Use __dict__.get to avoid recursive __getattr__ when _special_tokens_map
            # is not yet initialized (e.g. during fast tokenizer __init__)
            token_value = self.__dict__.get("_special_tokens_map", {}).get(key_without_id)
            if token_value is None:
                if self.verbose:
                    logger.error(f"Using {key}, but it is not set yet.")
                return None
            return self.convert_tokens_to_ids(str(token_value)) if key != key_without_id else str(token_value)

        # Extra special tokens
        if key_without_id == "extra_special_tokens":
            tokens = [str(tok) for tok in self.__dict__.get("_extra_special_tokens", [])]
            return self.convert_tokens_to_ids(tokens) if key != key_without_id else tokens

        if key not in self.__dict__:
            # Also check the class hierarchy (handles class-level defaults, e.g. in
            # dynamically loaded remote code where __getattr__ may be called before
            # the instance attribute is set)
            for cls in type(self).__mro__:
                if key in vars(cls):
                    return vars(cls)[key]
            raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")
        return object.__getattribute__(self, key)