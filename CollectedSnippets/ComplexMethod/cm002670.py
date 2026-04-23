def _patch_mistral_regex(
        cls,
        tokenizer,
        pretrained_model_name_or_path,
        token=None,
        cache_dir=None,
        local_files_only=False,
        _commit_hash=None,
        is_local=False,
        init_kwargs=None,
        fix_mistral_regex=None,
        **kwargs,
    ):
        """
        Patches mistral related tokenizers with incorrect regex if detected
            1) Local file with an associated config saved next to it
                >> Model type one of the mistral models (on older versions)
            2) Remote models on the hub from official mistral models
                >> Tags including `base_model:.*mistralai`
        """
        import re
        from functools import lru_cache

        from huggingface_hub import model_info
        from packaging import version

        from transformers.utils.hub import cached_file

        @lru_cache(maxsize=128)
        def is_base_mistral(model_id: str) -> bool:
            try:
                model = model_info(model_id)
            except Exception:
                # Never block tokenizer init on a Hub error — assume non-Mistral.
                return False
            if model.tags is not None:
                if re.search("base_model:.*mistralai", "".join(model.tags)):
                    return True
            return False

        if local_files_only or is_offline_mode():
            is_local = True

        if pretrained_model_name_or_path is not None and (
            is_local or (not is_local and is_base_mistral(pretrained_model_name_or_path))
        ):
            _config_file = cached_file(
                pretrained_model_name_or_path,
                "config.json",
                cache_dir=cache_dir,
                token=token,
                local_files_only=local_files_only,
                _raise_exceptions_for_missing_entries=False,
                _raise_exceptions_for_connection_errors=False,
                _commit_hash=_commit_hash,
            )

            # Detected using a (local) mistral tokenizer
            mistral_config_detected = False
            if _config_file is not None:
                with open(_config_file, encoding="utf-8") as f:
                    _config = json.load(f)
                transformers_version = _config.get("transformers_version")
                transformers_model_type = _config.get("model_type")

                # Detect if we can skip the mistral fix by
                #   a) having a non-mistral tokenizer
                #   b) fixed version of transformers
                if transformers_version and version.parse(transformers_version) < version.parse("5.0.0"):
                    if (
                        is_local
                        and transformers_model_type is not None
                        and transformers_model_type
                        not in [
                            "mistral",
                            "mistral3",
                            "voxtral",
                            "ministral",
                            "pixtral",
                        ]
                    ):
                        return tokenizer
                elif transformers_version and version.parse(transformers_version) >= version.parse("5.0.0"):
                    return tokenizer

                mistral_config_detected = True

            if mistral_config_detected or (not is_local and is_base_mistral(pretrained_model_name_or_path)):
                # Expose the `fix_mistral_regex` flag on the tokenizer when provided, even if no correction is applied.
                if init_kwargs and "fix_mistral_regex" in init_kwargs:
                    setattr(tokenizer, "fix_mistral_regex", init_kwargs["fix_mistral_regex"])

                # only warn if its not explicitly passed
                if fix_mistral_regex is None and not getattr(tokenizer, "fix_mistral_regex", False):
                    setattr(tokenizer, "fix_mistral_regex", False)
                    logger.warning(
                        f"The tokenizer you are loading from '{pretrained_model_name_or_path}'"
                        f" with an incorrect regex pattern: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503/discussions/84#69121093e8b480e709447d5e."
                        " This will lead to incorrect tokenization. You should set the `fix_mistral_regex=True` flag when loading this tokenizer to fix this issue."
                    )
                elif fix_mistral_regex is True or getattr(tokenizer, "fix_mistral_regex", False):
                    setattr(tokenizer, "fix_mistral_regex", True)
                    import tokenizers

                    split_pretokenizer = tokenizers.pre_tokenizers.Split(
                        pattern=tokenizers.Regex(
                            r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+"
                        ),
                        behavior="isolated",
                    )
                    current_pretokenizer = tokenizer.pre_tokenizer
                    # Check if it's already a Sequence
                    if isinstance(current_pretokenizer, tokenizers.pre_tokenizers.Sequence):
                        # Replace the first element (the Split pattern)
                        tokenizer.pre_tokenizer[0] = split_pretokenizer
                    else:
                        # Replace Metaspace with ByteLevel when adding Split, as Metaspace(split=False) doesn't
                        # work correctly with the Split pre-tokenizer and causes spaces to be lost during encoding
                        if isinstance(current_pretokenizer, tokenizers.pre_tokenizers.Metaspace):
                            current_pretokenizer = tokenizers.pre_tokenizers.ByteLevel(
                                add_prefix_space=False, use_regex=False
                            )

                        # Not a Sequence, so create one with Split + current pretokenizer
                        tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.Sequence(
                            [
                                split_pretokenizer,
                                current_pretokenizer,
                            ]
                        )

        return tokenizer