def convert_to_native_format(cls, trust_remote_code=False, **kwargs):
        """
        Build a `tokenizers.Tokenizer` backend from the available serialization files (tokenizer.json, sentencepiece
        models, tekken.json, vocab/merges).
        """
        # Preserve kwargs for possible downstream use
        local_kwargs = dict(kwargs)
        fast_tokenizer_file = local_kwargs.pop("tokenizer_file", None)

        if (
            fast_tokenizer_file is not None
            and os.path.isfile(fast_tokenizer_file)
            and (cls is TokenizersBackend or "__init__" not in cls.__dict__ or trust_remote_code)
        ):
            local_kwargs["tokenizer_object"] = TokenizerFast.from_file(fast_tokenizer_file)
            return local_kwargs
        elif fast_tokenizer_file is not None and os.path.isfile(fast_tokenizer_file):
            # we extract vocab/merges and pass decoder/pre_tokenizer/post_processor
            # from the file so the reconstructed tokenizer matches the tokenizer.json
            with open(fast_tokenizer_file, encoding="utf-8") as tokenizer_handle:
                tokenizer_json = json.load(tokenizer_handle)

            # Build a minimal tokenizer (empty vocab/merges) to cheaply extract post_processor,
            # padding and truncation as Rust objects — avoids parsing the full vocab via from_file.
            # This optimization applies to BPE, WordPiece, and WordLevel only:
            # - Unigram (SentencePiece) requires a non-empty vocab to initialize correctly in Rust
            #   (e.g. AlbertTokenizer, CamembertTokenizer, LlamaTokenizer, T5Tokenizer); passing an
            #   empty vocab causes "Unable to load vocab EmptyVocabulary". TODO: investigate if keeping
            #   just the UNK token is sufficient to make Unigram work with a minimal vocab.
            # - Older tokenizer.json formats (e.g. XLNetTokenizer, DistilBertTokenizer) omit the
            #   "type" field in the "model" section, so we cannot determine the model type from JSON.
            # In both cases we fall back to the original from_file path (no performance improvement).
            model_type = tokenizer_json.get("model", {}).get("type")
            if model_type not in (None, "Unigram"):
                minimal_tokenizer_json = dict(tokenizer_json)
                minimal_model = dict(tokenizer_json["model"])
                minimal_model["vocab"] = {}
                if model_type == "BPE":
                    minimal_model["merges"] = []
                minimal_tokenizer_json["model"] = minimal_model
                minimal_tokenizer_json["added_tokens"] = []
                tok_from_file = TokenizerFast.from_str(json.dumps(minimal_tokenizer_json))
            else:
                tok_from_file = TokenizerFast.from_file(fast_tokenizer_file)

            local_kwargs["post_processor"] = tok_from_file.post_processor
            local_kwargs["tokenizer_padding"] = tok_from_file.padding
            local_kwargs["tokenizer_truncation"] = tok_from_file.truncation
            # Preserve truncation and padding baked into tokenizer.json so that classes
            # with a custom __init__ that rebuild the backend tokenizer from scratch
            # can still access these settings.
            if tok_from_file.truncation is not None:
                local_kwargs["_json_truncation"] = tok_from_file.truncation
            if tok_from_file.padding is not None:
                local_kwargs["_json_padding"] = tok_from_file.padding

            # Extract precompiled SentencePiece charsmap from tokenizer.json normalizer
            # when present (e.g. T5 tokenizers converted with SentencePiece >= 2.x).
            normalizer_config = tokenizer_json.get("normalizer")
            if normalizer_config:
                if normalizer_config.get("type", None) == "Sequence":
                    normalizer_config = normalizer_config["normalizers"]
                elif not isinstance(normalizer_config, list):
                    normalizer_config = [normalizer_config]
                for normalizer in normalizer_config:
                    if normalizer.get("type") == "Precompiled" and "precompiled_charsmap" in normalizer:
                        import base64

                        local_kwargs["_spm_precompiled_charsmap"] = base64.b64decode(
                            normalizer["precompiled_charsmap"]
                        )
                        break

            vocab = tokenizer_json.get("model", {}).get("vocab", None)
            if cls.model is None:
                if isinstance(vocab, list):
                    vocab = list(map(tuple, vocab))  # TODO just for now
            elif cls.model.__name__ == "Unigram":
                if isinstance(vocab, list) and vocab and isinstance(vocab[0], (list, tuple)):
                    vocab = [tuple(item) for item in vocab]
            elif cls.model.__name__ == "WordLevel":
                vocab = {token: i for i, token in enumerate(vocab)}
            elif cls.model.__name__ == "BPE" or cls.model.__name__ == "WordPiece":
                if isinstance(vocab, list):
                    vocab = {token[0] if isinstance(token, list) else token: i for i, token in enumerate(vocab)}
            local_kwargs["vocab"] = vocab

            model_type = getattr(cls, "model", None)
            if "merges" in tokenizer_json.get("model", {}) and (model_type and model_type.__name__ == "BPE"):
                merges = tokenizer_json["model"]["merges"]
                merges = [tuple(merge.split(" ")) if isinstance(merge, str) else tuple(merge) for merge in merges]
                local_kwargs["merges"] = merges

            return local_kwargs

        vocab_file = local_kwargs.get("vocab_file")
        merges_file = local_kwargs.get("merges_file")
        vocab = local_kwargs.get("vocab")
        merges = local_kwargs.get("merges")

        # Tekken converter (Mistral)
        if isinstance(vocab_file, str) and vocab_file.endswith("tekken.json") and os.path.isfile(vocab_file):
            from .convert_slow_tokenizer import MistralConverter

            local_kwargs["vocab"], local_kwargs["merges"] = MistralConverter(
                vocab_file=vocab_file
            ).extract_vocab_merges_from_model(vocab_file)
            return local_kwargs

        # SentencePiece model (with TikToken fallback)
        if isinstance(vocab_file, str) and os.path.isfile(vocab_file) and vocab_file.endswith(".model"):
            try:
                from .convert_slow_tokenizer import SentencePieceExtractor

                # 1. Extract vocab, merges, and spm_precompiled from the .model proto
                extractor = SentencePieceExtractor(vocab_file)
                local_kwargs = extractor.extract(cls.model, **local_kwargs)

                # 2. If a model-specific converter exists, use it.
                try:
                    from .convert_slow_tokenizer import SLOW_TO_FAST_CONVERTERS

                    converter_class = SLOW_TO_FAST_CONVERTERS.get(cls.__name__)
                    if converter_class is not None and hasattr(converter_class, "convert_from_spm"):
                        local_kwargs = converter_class.convert_from_spm(**local_kwargs)
                except Exception as e:
                    logger.warning(
                        f"Could not reorder vocab using converter for {cls.__name__} due to {e}. Falling back to raw SentencePiece extraction."
                    )
                if hasattr(cls, "convert_from_spm_model"):
                    local_kwargs = cls.convert_from_spm_model(**local_kwargs)

                # 3. For non-model specific tokenizers (e.g. TokenizersBackend used
                #    for MODELS_WITH_INCORRECT_HUB_TOKENIZER_CLASS), build a _tokenizer
                #    from the proto so normalizer/decoder are configured correctly.
                if "tokenizer_object" not in local_kwargs and (
                    cls is TokenizersBackend or "__init__" not in cls.__dict__
                ):
                    vocab = local_kwargs.pop("vocab", None)
                    merges = local_kwargs.pop("merges", None)

                    # Replace placeholder tokens as specified in added_tokens_decoder
                    added_tokens_decoder = local_kwargs.get("added_tokens_decoder") or {}
                    if vocab is not None and added_tokens_decoder:
                        id_to_token = {token_id: token for token, token_id in vocab.items()}
                        for token_id, new_token in added_tokens_decoder.items():
                            token_id = int(token_id)
                            new_token = str(new_token)
                            current_token = id_to_token.get(token_id)
                            if current_token and current_token != new_token and new_token not in vocab:
                                vocab[new_token] = vocab.pop(current_token)
                                id_to_token[token_id] = new_token

                    tokenizer_object = SpmConverter.build_tokenizer_from_spm_proto(
                        proto=extractor.proto,
                        vocab=vocab,
                        merges=merges,
                    )
                    if tokenizer_object is not None:
                        local_kwargs["tokenizer_object"] = tokenizer_object
                        # Set bos/eos tokens from proto spec if available. This is needed when
                        # building a tokenizer_object directly from a .model file because the
                        # tokenizer_object does not have bos/eos set.
                        proto_spec = extractor.proto.trainer_spec
                        if proto_spec.bos_id >= 0:
                            local_kwargs.setdefault("bos_token", proto_spec.bos_piece or "<s>")
                        if proto_spec.eos_id >= 0:
                            local_kwargs.setdefault("eos_token", proto_spec.eos_piece or "</s>")
                        if proto_spec.unk_id >= 0:
                            local_kwargs.setdefault("unk_token", proto_spec.unk_piece or "<unk>")

            except Exception as e:  # TODO only catch deserialization error here!
                logger.warning(
                    f"Could not extract SentencePiece model from {vocab_file} using sentencepiece library due to {e}. "
                    "Falling back to TikToken extractor."
                )
                from .convert_slow_tokenizer import TikTokenConverter

                converter = TikTokenConverter(
                    vocab_file=vocab_file, extra_special_tokens=local_kwargs.get("extra_special_tokens")
                )
                local_kwargs["tokenizer_object"] = converter.converted()
            return local_kwargs

        # Fallback to standard vocab/merges files if they existed!
        if vocab is None and isinstance(vocab_file, str) and os.path.isfile(vocab_file):
            local_kwargs["vocab"] = vocab_file
            vocab = local_kwargs["vocab"]
        if merges is None and isinstance(merges_file, str) and os.path.isfile(merges_file):
            local_kwargs["merges"] = merges_file
            merges = local_kwargs["merges"]

        # Generate merges automatically when not provided for BPE tokenizers
        if merges is None and cls.model is not None and cls.model.__name__ == "BPE" and isinstance(vocab, dict):
            # Gather special tokens from kwargs to skip in merge generation
            def _iter_special_tokens(values: Iterable[Any]) -> list[str]:
                collected: list[str] = []
                for val in values:
                    if val is None:
                        continue
                    if isinstance(val, (list, tuple)):
                        collected.extend(_iter_special_tokens(val))
                    else:
                        collected.append(str(val))
                return collected

            special_tokens_keys = [
                "pad_token",
                "unk_token",
                "bos_token",
                "eos_token",
                "sep_token",
                "cls_token",
                "mask_token",
                "additional_special_tokens",
                "extra_special_tokens",
            ]
            skip_tokens: set[str] = set()
            for key in special_tokens_keys:
                if key in local_kwargs:
                    skip_tokens.update(_iter_special_tokens([local_kwargs[key]]))

            merges = generate_merges(vocab, skip_tokens=skip_tokens)
            local_kwargs["merges"] = merges
        return local_kwargs