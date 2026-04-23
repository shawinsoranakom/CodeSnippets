def add_special_tokens(
        self,
        special_tokens_dict: dict[str, str | AddedToken | Sequence[str | AddedToken]],
        replace_extra_special_tokens=True,
    ) -> int:
        """
        Add a dictionary of special tokens (eos, pad, cls, etc.) to the encoder and link them to class attributes. If
        special tokens are NOT in the vocabulary, they are added to it (indexed starting from the last index of the
        current vocabulary).

        When adding new tokens to the vocabulary, you should make sure to also resize the token embedding matrix of the
        model so that its embedding matrix matches the tokenizer.

        In order to do that, please use the [`~PreTrainedModel.resize_token_embeddings`] method.

        Using `add_special_tokens` will ensure your special tokens can be used in several ways:

        - Special tokens can be skipped when decoding using `skip_special_tokens = True`.
        - Special tokens are carefully handled by the tokenizer (they are never split), similar to `AddedTokens`.
        - You can easily refer to special tokens using tokenizer class attributes like `tokenizer.cls_token`. This
          makes it easy to develop model-agnostic training and fine-tuning scripts.

        When possible, special tokens are already registered for provided pretrained models (for instance
        [`BertTokenizer`] `cls_token` is already registered to be `'[CLS]'` and XLM's one is also registered to be
        `'</s>'`).

        Args:
            special_tokens_dict (dictionary *str* to *str*, `tokenizers.AddedToken`, or `Sequence[Union[str, AddedToken]]`):
                Keys should be in the list of predefined special attributes: [`bos_token`, `eos_token`, `unk_token`,
                `sep_token`, `pad_token`, `cls_token`, `mask_token`, `extra_special_tokens`].

                Tokens are only added if they are not already in the vocabulary (tested by checking if the tokenizer
                assign the index of the `unk_token` to them).
            replace_extra_special_tokens (`bool`, *optional*, defaults to `True`):
                If `True`, the existing list of extra special tokens will be replaced by the list provided in
                `special_tokens_dict`. Otherwise, `extra_special_tokens` will be extended. In the former
                case, the tokens will NOT be removed from the tokenizer's full vocabulary - they are only being flagged
                as non-special tokens. Remember, this only affects which tokens are skipped during decoding, not the
                `added_tokens_encoder` and `added_tokens_decoder`. This means that the previous
                `extra_special_tokens` are still added tokens, and will not be split by the model.

        Returns:
            `int`: Number of tokens added to the vocabulary.

        Examples:

        ```python
        # Let's see how to add a new classification token to GPT-2
        tokenizer = GPT2Tokenizer.from_pretrained("openai-community/gpt2")
        model = GPT2Model.from_pretrained("openai-community/gpt2")

        special_tokens_dict = {"cls_token": "<CLS>"}

        num_added_toks = tokenizer.add_special_tokens(special_tokens_dict)
        print("We have added", num_added_toks, "tokens")
        # Notice: resize_token_embeddings expect to receive the full size of the new vocabulary, i.e., the length of the tokenizer.
        model.resize_token_embeddings(len(tokenizer))

        assert tokenizer.cls_token == "<CLS>"
        ```"""
        if not special_tokens_dict:
            return 0

        # V5: Allowed keys are SPECIAL_TOKENS_ATTRIBUTES + "extra_special_tokens"
        # Backward compatibility: convert "additional_special_tokens" to "extra_special_tokens"
        special_tokens_dict = dict(special_tokens_dict)
        if "additional_special_tokens" in special_tokens_dict:
            special_tokens_dict.setdefault(
                "extra_special_tokens", special_tokens_dict.pop("additional_special_tokens")
            )

        allowed_keys = set(self.SPECIAL_TOKENS_ATTRIBUTES) | {"extra_special_tokens"}
        tokens_to_add = []
        for key, value in special_tokens_dict.items():
            if key not in allowed_keys:
                raise ValueError(f"Key {key} is not a valid special token. Valid keys are: {allowed_keys}")

            if self.verbose:
                logger.info(f"Assigning {value} to the {key} key of the tokenizer")

            if key == "extra_special_tokens":
                if not isinstance(value, (list, tuple)) or not all(isinstance(t, (str, AddedToken)) for t in value):
                    raise ValueError(f"Tokens {value} for key {key} should all be str or AddedToken instances")
                new_tokens = [
                    (
                        AddedToken(t, rstrip=False, lstrip=False, normalized=False, special=True)
                        if isinstance(t, str)
                        else t
                    )
                    for t in value
                    if replace_extra_special_tokens or str(t) not in self.extra_special_tokens
                ]
                if replace_extra_special_tokens and new_tokens:
                    self._extra_special_tokens = list(new_tokens)
                else:
                    self._extra_special_tokens.extend(new_tokens)
                tokens_to_add.extend(new_tokens)
            else:
                if not isinstance(value, (str, AddedToken)):
                    raise ValueError(f"Token {value} for key {key} should be a str or an AddedToken instance")
                if isinstance(value, str):
                    value = AddedToken(value, rstrip=False, lstrip=False, normalized=False, special=True)
                setattr(self, key, value)
                tokens_to_add.append(value)

        return self.add_tokens(tokens_to_add, special_tokens=True)