def _from_pretrained(
        cls,
        resolved_vocab_files,
        pretrained_model_name_or_path,
        init_configuration,
        *init_inputs,
        token=None,
        cache_dir=None,
        local_files_only=False,
        _commit_hash=None,
        _is_local=False,
        trust_remote_code=False,
        **kwargs,
    ):
        # Prepare tokenizer initialization kwargs
        # Did we saved some inputs and kwargs to reload ?
        tokenizer_config_file = resolved_vocab_files.pop("tokenizer_config_file", None)
        if tokenizer_config_file is not None:
            with open(tokenizer_config_file, encoding="utf-8") as tokenizer_config_handle:
                init_kwargs = json.load(tokenizer_config_handle)
            # used in the past to check if the tokenizer class matches the class in the repo
            init_kwargs.pop("tokenizer_class", None)
            saved_init_inputs = init_kwargs.pop("init_inputs", ())
            if not init_inputs:
                init_inputs = saved_init_inputs
        else:
            init_kwargs = init_configuration

        if resolved_vocab_files.get("tokenizer_file", None) is not None:
            init_kwargs.pop("add_bos_token", None)
            init_kwargs.pop("add_eos_token", None)

        # If independent chat template file(s) exist, they take priority over template entries in the tokenizer config
        chat_templates = {}
        chat_template_file = resolved_vocab_files.pop("chat_template_file", None)
        extra_chat_templates = [key for key in resolved_vocab_files if key.startswith("chat_template_")]
        if chat_template_file is not None:
            with open(chat_template_file, encoding="utf-8") as chat_template_handle:
                chat_templates["default"] = chat_template_handle.read()
        for extra_chat_template in extra_chat_templates:
            template_file = resolved_vocab_files.pop(extra_chat_template, None)
            if template_file is None:
                continue  # I think this should never happen, but just in case
            template_name = extra_chat_template.removeprefix("chat_template_")
            with open(template_file) as chat_template_handle:
                chat_templates[template_name] = chat_template_handle.read()
        if len(chat_templates) == 1 and "default" in chat_templates:
            init_kwargs["chat_template"] = chat_templates["default"]
        elif chat_templates:
            init_kwargs["chat_template"] = chat_templates

        if not _is_local:
            if "auto_map" in init_kwargs:
                # For backward compatibility with odl format.
                if isinstance(init_kwargs["auto_map"], (tuple, list)):
                    init_kwargs["auto_map"] = {"AutoTokenizer": init_kwargs["auto_map"]}

        # Update with newly provided kwargs
        init_kwargs.update(kwargs)

        # V5: Convert deprecated additional_special_tokens to extra_special_tokens
        if "additional_special_tokens" in init_kwargs:
            init_kwargs.setdefault("extra_special_tokens", init_kwargs.pop("additional_special_tokens"))

        # V5: Collect model-specific tokens (custom *_token keys not in standard attributes)
        default_attrs = set(cls.SPECIAL_TOKENS_ATTRIBUTES)
        model_specific_tokens = {
            key: init_kwargs.pop(key)
            for key in list(init_kwargs.keys())
            if key not in default_attrs and key.endswith("_token") and isinstance(init_kwargs[key], (str, AddedToken))
        }
        # If extra_special_tokens is a dict, merge it into model_specific_tokens
        if isinstance(init_kwargs.get("extra_special_tokens"), dict):
            model_specific_tokens.update(init_kwargs.pop("extra_special_tokens"))
        if model_specific_tokens:
            init_kwargs["model_specific_special_tokens"] = model_specific_tokens

        # Merge resolved_vocab_files arguments in init_kwargs.
        added_tokens_file = resolved_vocab_files.pop("added_tokens_file", None)
        special_tokens_map_file = resolved_vocab_files.pop("special_tokens_map_file", None)
        for args_name, file_path in resolved_vocab_files.items():
            if args_name not in init_kwargs or init_kwargs[args_name] is None:
                init_kwargs[args_name] = file_path
        tokenizer_file = resolved_vocab_files.get("tokenizer_file", None)

        init_kwargs["name_or_path"] = pretrained_model_name_or_path
        init_kwargs["is_local"] = _is_local
        init_kwargs["local_files_only"] = local_files_only

        #### Handle tokenizer serialization of added and special tokens
        added_tokens_decoder: dict[int, AddedToken] = {}
        added_tokens_map: dict[str, AddedToken] = {}
        # if we have info on the slow added tokens
        if "added_tokens_decoder" in init_kwargs:
            for idx, token in init_kwargs["added_tokens_decoder"].items():
                if isinstance(token, dict):
                    token = AddedToken(**token)
                if isinstance(token, AddedToken):
                    added_tokens_decoder[int(idx)] = token
                    added_tokens_map[str(token)] = token
                else:
                    raise TypeError(
                        f"Found a {token.__class__} in the saved `added_tokens_decoder`, should be a dictionary or an AddedToken instance"
                    )
        else:
            # Legacy: read special_tokens_map.json and merge into init_kwargs
            if special_tokens_map_file is not None:
                with open(special_tokens_map_file, encoding="utf-8") as f:
                    special_tokens_map = json.load(f)
                for key, value in special_tokens_map.items():
                    if key in kwargs and kwargs[key]:
                        continue  # User-provided kwargs take precedence
                    if isinstance(value, dict) and key != "extra_special_tokens":
                        value.pop("special", None)
                        value = AddedToken(**value, special=True)
                    elif key == "extra_special_tokens" and isinstance(value, list):
                        # Merge list tokens, converting dicts to AddedToken
                        existing = list(init_kwargs.get("extra_special_tokens") or [])
                        for tok in value:
                            tok = AddedToken(**tok, special=True) if isinstance(tok, dict) else tok
                            if tok not in existing:
                                existing.append(tok)
                        value = existing
                    init_kwargs[key] = value
                # Convert dict extra_special_tokens to model_specific_special_tokens
                if isinstance(init_kwargs.get("extra_special_tokens"), dict):
                    init_kwargs.setdefault("model_specific_special_tokens", {}).update(
                        init_kwargs.pop("extra_special_tokens")
                    )

            # slow -> slow|fast, legacy: convert the `"added_tokens.json"` file to `added_tokens_decoder`.
            # this is for legacy purpose. We don't add the tokens after init for efficiency.
            if added_tokens_file is not None:
                # V5: Check both named and extra special tokens
                special_tokens = {str(init_kwargs[k]) for k in cls.SPECIAL_TOKENS_ATTRIBUTES if init_kwargs.get(k)}
                special_tokens.update(str(t) for t in (init_kwargs.get("extra_special_tokens") or []))

                with open(added_tokens_file, encoding="utf-8") as f:
                    added_tok_encoder = json.load(f)
                for str_token, index in added_tok_encoder.items():
                    is_special = str_token in special_tokens
                    added_tokens_decoder[index] = AddedToken(
                        str_token, rstrip=False, lstrip=False, normalized=not is_special, special=is_special
                    )
                    added_tokens_map[str_token] = added_tokens_decoder[index]

            # allows converting a fast -> slow: add the `tokenizer.json`'s `"added_tokens"` to the slow tokenizer
            # if `tokenizer_config.json` is `None`
            if tokenizer_file is not None:
                # This is for slow so can be done before
                with open(tokenizer_file, encoding="utf-8") as tokenizer_file_handle:
                    tokenizer_file_handle = json.load(tokenizer_file_handle)
                    added_tokens = tokenizer_file_handle.pop("added_tokens")
                for serialized_tokens in added_tokens:
                    idx = serialized_tokens.pop("id")
                    added_tokens_decoder[idx] = AddedToken(**serialized_tokens)
                    added_tokens_map[str(added_tokens_decoder[idx])] = added_tokens_decoder[idx]
            # end legacy

        # Passing AddedTokens and not strings to the class to prevent it from casting the string to a different AddedToken
        # convert {'__type': 'AddedToken', 'content': '<ent>', 'lstrip': False, 'normalized': True, ...} to AddedTokens
        init_kwargs["added_tokens_decoder"] = added_tokens_decoder
        init_kwargs = cls.convert_added_tokens(init_kwargs, save=False)
        # V5: Map special tokens from added_tokens_map (named tokens only)
        for key in cls.SPECIAL_TOKENS_ATTRIBUTES:
            if key in init_kwargs and added_tokens_map != {} and init_kwargs[key] is not None:
                init_kwargs[key] = added_tokens_map.get(str(init_kwargs[key]), init_kwargs[key])

        # From pretrained with the legacy fixes
        # for `tokenizers` based tokenizer, we actually want to have vocab and merges pre-extracted from whatever inputs
        # for `none` (PythonBackend) based tokenizer, we also want the vocab file / merge files not extracted.
        # for `sentencepiece` based tokenizer, we pass the sentencepiece model file directly.
        init_kwargs = cls.convert_to_native_format(**init_kwargs)

        try:
            tokenizer = cls(*init_inputs, **init_kwargs)
        except import_protobuf_decode_error():
            raise RuntimeError(
                "Unable to load tokenizer model from SPM, loading from TikToken will be attempted instead."
                "(Google protobuf error: Tried to load SPM model with non-SPM vocab file).",
            )
        except RuntimeError as e:
            if "sentencepiece_processor.cc" in str(e):
                raise RuntimeError(
                    "Unable to load tokenizer model from SPM, loading from TikToken will be attempted instead."
                    "(SentencePiece RuntimeError: Tried to load SPM model with non-SPM vocab file).",
                ) from e
            else:
                raise e
        except OSError:
            raise OSError(
                "Unable to load vocabulary from file. "
                "Please check that the provided vocabulary is accessible and not corrupted."
            )
        return tokenizer