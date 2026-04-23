def __init__(
        self,
        rec_char_dict_path,
        max_seq_len,
        **kwargs,
    ):
        # Set the TOKENIZERS_PARALLELISM environment variable to 'false' to suppress
        # the warning: "The current process just got forked, Disabling parallelism to avoid deadlocks..
        #  To disable this warning, please explicitly set TOKENIZERS_PARALLELISM=(true | false)" from tokenizers
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        from tokenizers import Tokenizer as TokenizerFast
        from tokenizers import AddedToken

        self._unk_token = "<unk>"
        self._bos_token = "<s>"
        self._eos_token = "</s>"
        self._pad_token = "<pad>"
        self._sep_token = None
        self._cls_token = None
        self._mask_token = None
        self._additional_special_tokens = []
        self.model_input_names = ["input_ids", "token_type_ids", "attention_mask"]
        self.max_seq_len = max_seq_len
        self.pad_token_id = 1
        self.bos_token_id = 0
        self.eos_token_id = 2
        self.padding_side = "right"
        self.pad_token = "<pad>"
        self.pad_token_type_id = 0
        self.pad_to_multiple_of = None
        fast_tokenizer_file = os.path.join(rec_char_dict_path, "tokenizer.json")
        tokenizer_config_file = os.path.join(
            rec_char_dict_path, "tokenizer_config.json"
        )
        self.tokenizer = TokenizerFast.from_file(fast_tokenizer_file)
        added_tokens_decoder = {}
        added_tokens_map = {}

        if tokenizer_config_file is not None:
            with open(
                tokenizer_config_file, encoding="utf-8"
            ) as tokenizer_config_handle:
                init_kwargs = json.load(tokenizer_config_handle)
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