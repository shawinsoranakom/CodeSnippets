def tokenizer(self, proto):
        model_type = proto.trainer_spec.model_type
        vocab_scores = self.vocab(proto)

        if model_type == 1:
            tokenizer = Tokenizer(
                Unigram(
                    vocab_scores,
                    unk_id=self.unk_id(proto),
                    byte_fallback=self.handle_byte_fallback,
                )
            )

        elif model_type == 2:
            _, merges = self.SpmExtractor(self.original_tokenizer.vocab_file).extract(vocab_scores)
            bpe_vocab = {word: i for i, (word, score) in enumerate(vocab_scores)}
            tokenizer = Tokenizer(
                BPE(
                    bpe_vocab,
                    merges,
                    unk_token=proto.trainer_spec.unk_piece,
                    fuse_unk=True,
                    byte_fallback=self.handle_byte_fallback,
                    dropout=None,
                )
            )

        else:
            raise Exception(
                "You're trying to run a `Unigram` model but you're file was trained with a different algorithm"
            )

        # control tokens are special
        # user defined symbols are not
        # both user and control tokens are AddedTokens
        # Add user defined symbols (type == 4) from sentencepiece (https://github.com/google/sentencepiece/blob/6225e08edb2577757163b3f5dbba4c0b670ef445/src/sentencepiece_model.proto#L299C29-L299C33)
        spm_added_tokens = [
            (id, p.piece, p.type == 3 or p.piece in self.special_tokens)
            for id, p in enumerate(proto.pieces)
            if p.type in [3, 4]
        ]
        tokenizer.add_tokens(
            [
                AddedToken(token, normalized=False, special=special)
                for id, token, special in sorted(spm_added_tokens, key=lambda x: x[0])
            ]
        )

        return tokenizer