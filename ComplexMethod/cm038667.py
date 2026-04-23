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