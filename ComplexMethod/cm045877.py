def __init__(
            self,
            character_list: Dict[str, Any],
            **kwargs,
    ) -> None:
        """Initializes the UniMERNetDecode class.

        Args:
            character_list (Dict[str, Any]): Dictionary containing tokenizer configuration.
            **kwargs: Additional keyword arguments.
        """

        self._unk_token = "<unk>"
        self._bos_token = "<s>"
        self._eos_token = "</s>"
        self._pad_token = "<pad>"
        self._sep_token = None
        self._cls_token = None
        self._mask_token = None
        self._additional_special_tokens = []
        self.model_input_names = ["input_ids", "token_type_ids", "attention_mask"]
        self.max_seq_len = 2048
        self.pad_token_id = 1
        self.bos_token_id = 0
        self.eos_token_id = 2
        self.padding_side = "right"
        self.pad_token_id = 1
        self.pad_token = "<pad>"
        self.pad_token_type_id = 0
        self.pad_to_multiple_of = None

        fast_tokenizer_str = json.dumps(character_list["fast_tokenizer_file"])
        fast_tokenizer_buffer = fast_tokenizer_str.encode("utf-8")
        self.tokenizer = TokenizerFast.from_buffer(fast_tokenizer_buffer)
        tokenizer_config = (
            character_list["tokenizer_config_file"]
            if "tokenizer_config_file" in character_list
            else None
        )
        added_tokens_decoder = {}
        added_tokens_map = {}
        if tokenizer_config is not None:
            init_kwargs = tokenizer_config
            if "added_tokens_decoder" in init_kwargs:
                for idx, token in init_kwargs["added_tokens_decoder"].items():
                    if isinstance(token, dict):
                        token = AddedToken(**token)
                    if isinstance(token, AddedToken):
                        added_tokens_decoder[int(idx)] = token
                        added_tokens_map[str(token)] = token
                    else:
                        raise ValueError(
                            f"Found a {token.__class__} in the saved `added_tokens_decoder`, should be a dictionary or an AddedToken instance"
                        )
            init_kwargs["added_tokens_decoder"] = added_tokens_decoder
            added_tokens_decoder = init_kwargs.pop("added_tokens_decoder", {})
            tokens_to_add = [
                token
                for index, token in sorted(
                    added_tokens_decoder.items(), key=lambda x: x[0]
                )
                if token not in added_tokens_decoder
            ]
            added_tokens_encoder = self.added_tokens_encoder(added_tokens_decoder)
            encoder = list(added_tokens_encoder.keys()) + [
                str(token) for token in tokens_to_add
            ]
            tokens_to_add += [
                token
                for token in self.all_special_tokens_extended
                if token not in encoder and token not in tokens_to_add
            ]
            if len(tokens_to_add) > 0:
                is_last_special = None
                tokens = []
                special_tokens = self.all_special_tokens
                for token in tokens_to_add:
                    is_special = (
                        (token.special or str(token) in special_tokens)
                        if isinstance(token, AddedToken)
                        else str(token) in special_tokens
                    )
                    if is_last_special is None or is_last_special == is_special:
                        tokens.append(token)
                    else:
                        self._add_tokens(tokens, special_tokens=is_last_special)
                        tokens = [token]
                    is_last_special = is_special
                if tokens:
                    self._add_tokens(tokens, special_tokens=is_last_special)