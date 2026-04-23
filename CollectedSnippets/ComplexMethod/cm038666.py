def get_score_prompt(
        self,
        data_1: ScoreData,
        data_2: ScoreData,
        encode_kwargs: dict[str, Any],
        chat_template: str | None = None,
        max_tokens_per_query: int = 0,
        max_tokens_per_doc: int = 0,
    ):
        model_config = self.model_config
        tokenizer = self.tokenizer

        prompt_1, prompt_2, mm_data, mm_uuids = parse_score_data(
            data_1,
            data_2,
            model_config,
        )

        # Apply truncation before defining closures
        if max_tokens_per_query > 0 and isinstance(prompt_1, str):
            prompt_1 = truncate_text_to_tokens(
                prompt_1, tokenizer, max_tokens_per_query
            )
        if max_tokens_per_doc > 0 and isinstance(prompt_2, str):
            prompt_2 = truncate_text_to_tokens(prompt_2, tokenizer, max_tokens_per_doc)

        def default_tokenizer_encode():
            local_kwargs = encode_kwargs.copy()

            if self.supports_score_template:
                assert self.model is not None
                full_prompt = self.model.get_score_template(prompt_1, prompt_2)
                if full_prompt is None:
                    raise ValueError("Get empty score template from model")

                prompt_inputs = tokenizer(full_prompt, **local_kwargs)
            else:
                if self.use_sep_token:
                    # cross_encoder models defaults to using separating token.
                    if max_tokens_per_doc > 0 and isinstance(prompt_2, str):
                        query_tokens = tokenizer.encode(
                            prompt_1, add_special_tokens=False
                        )
                        num_special = get_num_special_tokens_for_pair(tokenizer)
                        doc_limit_max_length = (
                            len(query_tokens) + max_tokens_per_doc + num_special
                        )
                        existing_max_length = local_kwargs.get("max_length")
                        if existing_max_length is not None:
                            effective_max_length = min(
                                doc_limit_max_length, existing_max_length
                            )
                        else:
                            effective_max_length = doc_limit_max_length
                        local_kwargs["truncation"] = "only_second"
                        local_kwargs["max_length"] = effective_max_length

                    prompt_inputs = tokenizer(
                        text=prompt_1, text_pair=prompt_2, **local_kwargs
                    )
                    full_prompt = tokenizer.decode(prompt_inputs["input_ids"])
                else:
                    # `llm as reranker` defaults to not using separating token.
                    if max_tokens_per_doc > 0 and isinstance(prompt_2, str):
                        query_ids = tokenizer.encode(prompt_1, add_special_tokens=False)
                        doc_ids = tokenizer.encode(prompt_2, add_special_tokens=False)
                        doc_ids = doc_ids[:max_tokens_per_doc]
                        input_ids = query_ids + doc_ids
                        full_prompt = tokenizer.decode(input_ids)
                        prompt_inputs = {"input_ids": input_ids}
                    else:
                        full_prompt = prompt_1 + prompt_2
                        prompt_inputs = tokenizer(text=full_prompt, **local_kwargs)
            return full_prompt, prompt_inputs

        # FIXME: For now, we only apply a template when one is explicitly provided.
        # We cannot rely on the tokenizer's chat template because many models
        # inherit junk templates from their base LLM, which breaks both the models
        # and the tests that use them.
        if chat_template is None:
            full_prompt, prompt_inputs = default_tokenizer_encode()
        else:
            # FIXME:
            # Try applying a score template from the CLI arg or tokenizer_config.json
            # If that fails because there is no such template,
            # fall back to the default implementation.
            try:
                full_prompt = safe_apply_chat_template(
                    model_config,
                    tokenizer,
                    [
                        {"role": "query", "content": prompt_1},
                        {"role": "document", "content": prompt_2},
                    ],
                    chat_template=chat_template,
                    tools=None,
                    tokenize=False,
                )
                prompt_inputs = tokenizer(full_prompt, **encode_kwargs)
            except ChatTemplateResolutionError:
                full_prompt, prompt_inputs = default_tokenizer_encode()

        engine_prompt = TokensPrompt(prompt_token_ids=prompt_inputs["input_ids"])

        if (token_type_ids := prompt_inputs.get("token_type_ids")) is not None:
            engine_prompt["token_type_ids"] = token_type_ids

        if self.model is not None:
            self.model.post_process_tokens(engine_prompt)

        if mm_data is not None:
            engine_prompt["multi_modal_data"] = mm_data
        if mm_uuids is not None:
            engine_prompt["multi_modal_uuids"] = mm_uuids

        return full_prompt, engine_prompt