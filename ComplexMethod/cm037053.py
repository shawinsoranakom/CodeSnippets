def _validate_structured_outputs(
        self,
        structured_outputs_config: StructuredOutputsConfig | None,
        tokenizer: TokenizerLike | None,
    ) -> None:
        if structured_outputs_config is None or self.structured_outputs is None:
            return

        if tokenizer is None:
            raise ValueError(
                "Structured outputs requires a tokenizer so it can't be used with 'skip_tokenizer_init'"  # noqa: E501
            )

        backend = structured_outputs_config.backend
        if _backend := self.structured_outputs._backend:
            # Request-level backend selection is not supported.
            # The values may differ if `params` is reused and was set
            # to a specific backend based on `auto` behavior in a previous
            # request. We remember that it was set as a result of `auto`
            # using the `_backend_was_auto` field set in the params.
            if backend != _backend and not (
                backend == "auto" and self.structured_outputs._backend_was_auto
            ):
                raise ValueError(
                    "Request-level structured output backend selection is not "
                    f"supported. The request specified '{_backend}', but vLLM "
                    f"was initialised with '{backend}'. This error can be "
                    "resolved by removing '_backend' from the request."
                )
        else:
            self.structured_outputs._backend = backend

        # Request content validation
        if (
            isinstance(self.structured_outputs.choice, list)
            and not self.structured_outputs.choice
        ):
            # It is invalid for choice to be an empty list
            raise ValueError(
                f"Choice '{self.structured_outputs.choice}' cannot be an empty list"  # noqa: E501
            )
        # Reject empty string grammar early to avoid engine-side crashes
        if (
            isinstance(self.structured_outputs.grammar, str)
            and self.structured_outputs.grammar.strip() == ""
        ):
            raise ValueError("structured_outputs.grammar cannot be an empty string")

        from vllm.v1.structured_output.backend_guidance import (
            has_guidance_unsupported_json_features,
            validate_guidance_grammar,
        )
        from vllm.v1.structured_output.backend_lm_format_enforcer import (
            validate_structured_output_request_lm_format_enforcer,
        )
        from vllm.v1.structured_output.backend_outlines import (
            validate_structured_output_request_outlines,
        )
        from vllm.v1.structured_output.backend_xgrammar import validate_xgrammar_grammar

        if backend.startswith("xgrammar"):
            # xgrammar with no fallback
            validate_xgrammar_grammar(self)
        elif backend.startswith("guidance"):
            if _is_non_tekken_mistral(tokenizer=tokenizer):
                raise ValueError(
                    "Non-tekken Mistral tokenizers are not supported for the 'guidance'"
                    " structured output backend. Please either use a more recent "
                    "Mistral model, the ['xgrammar', 'outlines'] "
                    "backends or tokenizer_mode='hf' instead."
                )
            # TODO: ideally we would have the LLTokenizer here as Lark syntax
            # allows <|special_token|> and similar, see
            # https://github.com/guidance-ai/llguidance/blob/main/docs/syntax.md#special-tokens
            # Without tokenizer these are disallowed in grammars.
            validate_guidance_grammar(
                self,
                tokenizer=_get_llg_tokenizer(tokenizer),
            )
        elif backend == "outlines":
            # outlines backend
            validate_structured_output_request_outlines(self)
        elif backend == "lm-format-enforcer":
            # lm format enforcer backend
            if is_mistral_tokenizer(tokenizer):
                raise ValueError(
                    "Mistral tokenizer is not supported for the 'lm-format-enforcer' "
                    "structured output backend. Please use ['xgrammar', 'outlines'] "
                    "backends or tokenizer_mode='hf' instead."
                )
            validate_structured_output_request_lm_format_enforcer(self)
        else:
            # NOTE: backend must be "auto" here, because we have
            # checked supported_backends above.
            # In this mode, we set opinionated defaults based on what we think
            # will satisfy the most use cases without having to worry about
            # this setting. We include fallback behavior here, but not with any
            # other setting where a specific backend was specified.
            try:
                validate_xgrammar_grammar(self)
                self.structured_outputs._backend = "xgrammar"
            except ValueError:
                # The request either failed validation
                # or includes some jsonschema feature(s) that
                # are not supported in xgrammar.

                skip_guidance = _is_non_tekken_mistral(tokenizer)

                # Check if schema has features unsupported by guidance
                so_params = self.structured_outputs
                if not skip_guidance and so_params.json:
                    if isinstance(so_params.json, str):
                        schema = json_mod.loads(so_params.json)
                    else:
                        schema = so_params.json
                    skip_guidance = has_guidance_unsupported_json_features(schema)

                if skip_guidance:
                    # Fall back to outlines if the tokenizer is non-tekken Mistral or
                    # the schema contains features unsupported by guidance
                    validate_structured_output_request_outlines(self)
                    self.structured_outputs._backend = "outlines"
                else:
                    # Fall back to guidance by default.
                    validate_guidance_grammar(
                        self,
                        tokenizer=_get_llg_tokenizer(tokenizer),
                    )
                    self.structured_outputs._backend = "guidance"
            # Remember that this backend was set automatically
            self.structured_outputs._backend_was_auto = True

        # Run post-init validation. This is also important to ensure subsequent
        # roundtrip serialization/deserialization won't fail.
        self.structured_outputs.__post_init__()