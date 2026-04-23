def build_tokenizer_from_spm_proto(proto, vocab, merges=None):
        """
        Similar to convert_from_spm method, but used only when there is no `model_type` class, i.e. there is no matching class in `TOKENIZERS_MAPPING` and we just create a tokenizer instead of extracting stuff from the sentencepiece file
        """
        byte_fallback = proto.trainer_spec.byte_fallback
        unk_piece = proto.trainer_spec.unk_piece
        precompiled_charsmap = proto.normalizer_spec.precompiled_charsmap

        # model
        if isinstance(vocab, dict):
            tokenizer = Tokenizer(
                BPE(
                    vocab=vocab,
                    merges=merges or [],
                    unk_token=unk_piece,
                    fuse_unk=True,
                    byte_fallback=byte_fallback,
                    dropout=None,
                )
            )
        elif isinstance(vocab, list) and vocab and isinstance(vocab[0], tuple | list):
            tokenizer = Tokenizer(
                Unigram(
                    vocab=vocab,
                    unk_id=proto.trainer_spec.unk_id,
                    byte_fallback=byte_fallback,
                )
            )
        else:
            return None

        # normalizer
        _normalizers = [normalizers.Replace(" ", "▁")]
        if precompiled_charsmap:
            _normalizers.insert(0, normalizers.Precompiled(precompiled_charsmap))
        tokenizer.normalizer = normalizers.Sequence(_normalizers)

        # decoder
        if byte_fallback:
            tokenizer.decoder = decoders.Sequence(
                [decoders.Replace("▁", " "), decoders.ByteFallback(), decoders.Fuse()]
            )
        else:
            tokenizer.decoder = decoders.Sequence([decoders.Replace("▁", " ")])

        return tokenizer