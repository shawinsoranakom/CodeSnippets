def _sanitize_parameters(
        self,
        return_full_text=None,
        return_tensors=None,
        return_text=None,
        return_type=None,
        clean_up_tokenization_spaces=None,
        prefix=None,
        handle_long_generation=None,
        stop_sequence=None,
        truncation=None,
        max_length=None,
        continue_final_message=None,
        skip_special_tokens=None,
        tokenizer_encode_kwargs=None,
        tools=None,
        documents=None,
        **generate_kwargs,
    ):
        # preprocess kwargs
        preprocess_params = {}
        add_special_tokens = False
        if "add_special_tokens" in generate_kwargs:
            add_special_tokens = preprocess_params["add_special_tokens"] = generate_kwargs.pop("add_special_tokens")

        if "padding" in generate_kwargs:
            preprocess_params["padding"] = generate_kwargs.pop("padding")

        if truncation is not None:
            preprocess_params["truncation"] = truncation

        if max_length is not None:
            preprocess_params["max_length"] = max_length
            generate_kwargs["max_length"] = max_length

        if tools is not None:
            preprocess_params["tools"] = tools
        if documents is not None:
            preprocess_params["documents"] = documents

        if prefix is not None:
            preprocess_params["prefix"] = prefix
        if prefix:
            prefix_inputs = self.tokenizer(
                prefix, padding=False, add_special_tokens=add_special_tokens, return_tensors="pt"
            )
            generate_kwargs["prefix_length"] = prefix_inputs["input_ids"].shape[-1]

        if handle_long_generation is not None:
            if handle_long_generation != "hole":
                raise ValueError(
                    f"{handle_long_generation} is not a valid value for `handle_long_generation` parameter expected"
                    " [None, 'hole']"
                )
            preprocess_params["handle_long_generation"] = handle_long_generation

        if continue_final_message is not None:
            preprocess_params["continue_final_message"] = continue_final_message

        if tokenizer_encode_kwargs is not None:
            preprocess_params["tokenizer_encode_kwargs"] = tokenizer_encode_kwargs

        preprocess_params.update(generate_kwargs)

        # forward kwargs
        if stop_sequence is not None:
            stop_sequence_ids = self.tokenizer.encode(stop_sequence, add_special_tokens=False)
            generate_kwargs["eos_token_id"] = stop_sequence_ids
        forward_params = generate_kwargs
        if self.assistant_model is not None:
            forward_params["assistant_model"] = self.assistant_model
        if self.assistant_tokenizer is not None:
            forward_params["tokenizer"] = self.tokenizer
            forward_params["assistant_tokenizer"] = self.assistant_tokenizer

        # postprocess kwargs
        postprocess_params = {}
        if return_full_text is not None and return_type is None:
            if return_text is not None:
                raise ValueError("`return_text` is mutually exclusive with `return_full_text`")
            if return_tensors is not None:
                raise ValueError("`return_full_text` is mutually exclusive with `return_tensors`")
            return_type = ReturnType.FULL_TEXT if return_full_text else ReturnType.NEW_TEXT
        if return_tensors is not None and return_type is None:
            if return_text is not None:
                raise ValueError("`return_text` is mutually exclusive with `return_tensors`")
            return_type = ReturnType.TENSORS
        if return_type is not None:
            postprocess_params["return_type"] = return_type
        if clean_up_tokenization_spaces is not None:
            postprocess_params["clean_up_tokenization_spaces"] = clean_up_tokenization_spaces
        if continue_final_message is not None:
            postprocess_params["continue_final_message"] = continue_final_message
        if skip_special_tokens is not None:
            postprocess_params["skip_special_tokens"] = skip_special_tokens

        return preprocess_params, forward_params, postprocess_params