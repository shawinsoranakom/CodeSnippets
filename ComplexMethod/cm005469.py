def tokenizer(self, proto):
        vocab_scores = self.vocab(self.proto)
        merges = self.merges(self.proto)
        bpe_vocab = {word: i for i, (word, _score) in enumerate(vocab_scores)}

        unk_token = proto.tokens[proto.unk_token_id] if proto.unk_token_id is not None else None
        bos_token = proto.tokens[proto.bos_token_id] if getattr(proto, "bos_token_id", None) is not None else None
        eos_token = proto.tokens[proto.bos_token_id] if getattr(proto, "eos_token_id", None) is not None else None

        tokenizer = Tokenizer(
            BPE(
                bpe_vocab,
                merges,
                unk_token=unk_token,
                fuse_unk=True,
                byte_fallback=True,
            )
        )

        special_tokens = []

        if not hasattr(self.proto, "token_type"):
            if unk_token is not None:
                special_tokens.append(AddedToken(unk_token, normalized=False, special=True))

            if bos_token is not None:
                special_tokens.append(AddedToken(bos_token, normalized=False, special=True))

            if eos_token is not None:
                special_tokens.append(AddedToken(eos_token, normalized=False, special=True))
        else:
            # 3 stands for special tokens
            special_tokens_idx = np.where(np.array(self.proto.token_type) == 3)[0]

            for idx in special_tokens_idx:
                special_tokens.append(AddedToken(self.proto.tokens[idx], normalized=False, special=True))

        if len(special_tokens) != 0:
            tokenizer.add_special_tokens(special_tokens)

        if len(self.proto.added_tokens) != 0:
            tokenizer.add_tokens(
                [AddedToken(added_token, normalized=False, special=False) for added_token in self.proto.added_tokens]
            )

        self.additional_kwargs["unk_token"] = unk_token
        self.additional_kwargs["eos_token"] = bos_token
        self.additional_kwargs["bos_token"] = eos_token

        if self.is_llama_3_tokenizer:
            self.additional_kwargs["add_prefix_space"] = None
            self.additional_kwargs["clean_up_tokenization_spaces"] = True

            self.additional_kwargs["legacy"] = False
            self.original_tokenizer.legacy = False

        return tokenizer