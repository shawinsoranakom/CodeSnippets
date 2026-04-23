def extract(self, model_type, **kwargs) -> tuple[dict[str, int], list[tuple]]:
        """
        By default will return vocab and merges with respect to their order, by sending `vocab_scores` we're going to
        order the merges with respect to the piece scores instead.
        """
        self.proto.trainer_spec.unk_id
        if model_type is None:
            from tokenizers.models import BPE, Unigram

            model_type = Unigram if self.proto.trainer_spec.model_type == 1 else BPE
        vocab = [(piece.piece, piece.score) for piece in self.proto.pieces]

        if model_type.__name__ != "BPE":
            kwargs["unk_id"] = self.proto.trainer_spec.unk_id
            kwargs["vocab"] = vocab
        else:
            from .tokenization_utils_base import generate_merges

            vocab = {word: i for i, (word, score) in enumerate(vocab)}
            merges = generate_merges(vocab)
            kwargs["vocab"] = vocab
            kwargs["merges"] = merges

        # control tokens are special
        # user defined symbols are not
        # both user and control tokens are AddedTokens
        # Add user defined symbols (type == 4) from sentencepiece (https://github.com/google/sentencepiece/blob/6225e08edb2577757163b3f5dbba4c0b670ef445/src/sentencepiece_model.proto#L299C29-L299C33)
        spm_added_tokens = [(id, p.piece, p.type == 3) for id, p in enumerate(self.proto.pieces) if p.type in [3, 4]]
        kwargs["additional_special_tokens"] = [
            AddedToken(token, normalized=False, special=special)
            for id, token, special in sorted(spm_added_tokens, key=lambda x: x[0])
        ]
        kwargs["_spm_precompiled_charsmap"] = getattr(self.proto.normalizer_spec, "precompiled_charsmap", None)
        return kwargs