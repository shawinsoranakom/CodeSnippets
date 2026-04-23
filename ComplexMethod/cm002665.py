def _post_init(self):
        """
        Post-initialization hook that runs after the tokenizer is fully set up.
        This is called by from_pretrained() after loading the tokenizer, which allows
        us to add any special tokens that may have been passed as AddedToken objects.

        Child classes should call super()._post_init() if they override this method.
        """
        tokens_to_add = []
        # V5: Check named special tokens
        for token_value in self._special_tokens_map.values():
            if token_value is None:
                continue
            if isinstance(token_value, AddedToken):
                tokens_to_add.append(token_value)
            elif isinstance(token_value, str):
                tokens_to_add.append(AddedToken(token_value, special=True, normalized=False))

        # V5: Check extra special tokens
        for token in self._extra_special_tokens:
            if isinstance(token, AddedToken):
                tokens_to_add.append(token)
            elif isinstance(token, str):
                tokens_to_add.append(AddedToken(token, special=True, normalized=False))

        if tokens_to_add:
            # Ensure special tokens are added as such to the backend
            self.add_tokens(tokens_to_add, special_tokens=True)

        if getattr(self, "_should_update_post_processor", True) or self._tokenizer.post_processor is None:
            self.update_post_processor()