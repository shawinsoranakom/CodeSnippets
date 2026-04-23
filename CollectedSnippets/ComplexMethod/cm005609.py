def _sanitize_parameters(
        self,
        max_new_tokens=None,
        generate_kwargs=None,
        timeout=None,
        return_full_text=None,
        return_tensors=None,
        return_type=None,
        clean_up_tokenization_spaces=None,
        stop_sequence=None,
        continue_final_message=None,
        skip_special_tokens=None,
        processor_kwargs=None,
        **kwargs: Unpack[ProcessingKwargs],
    ):
        forward_kwargs = {}
        preprocess_params = {}
        postprocess_params = {}

        # Preprocess params
        preprocess_params.update(kwargs)
        if timeout is not None:
            preprocess_params["timeout"] = timeout
        if continue_final_message is not None:
            preprocess_params["continue_final_message"] = continue_final_message
        if processor_kwargs is not None:
            preprocess_params["processor_kwargs"] = processor_kwargs

        # Forward kwargs
        if generate_kwargs is not None:
            forward_kwargs["generate_kwargs"] = generate_kwargs
        if stop_sequence is not None:
            stop_sequence_ids = self.processor.tokenizer.encode(stop_sequence, add_special_tokens=False)
            if len(stop_sequence_ids) > 1:
                logger.warning_once(
                    "Stopping on a multiple token sequence is not yet supported on transformers. The first token of"
                    " the stop sequence will be used as the stop sequence string in the interim."
                )
            generate_kwargs["eos_token_id"] = stop_sequence_ids[0]
        if generate_kwargs is not None:
            forward_kwargs["generate_kwargs"] = generate_kwargs
        if max_new_tokens is not None:
            if "generate_kwargs" not in forward_kwargs:
                forward_kwargs["generate_kwargs"] = {}
            if "max_new_tokens" in forward_kwargs["generate_kwargs"]:
                raise ValueError(
                    "'max_new_tokens' is defined twice, once in 'generate_kwargs' and once as a direct parameter,"
                    " please use only one"
                )
            forward_kwargs["generate_kwargs"]["max_new_tokens"] = max_new_tokens

        # Postprocess params
        if return_full_text is not None and return_type is None:
            if return_tensors is not None:
                raise ValueError("`return_full_text` is mutually exclusive with `return_tensors`")
            return_type = ReturnType.FULL_TEXT if return_full_text else ReturnType.NEW_TEXT
        if return_tensors is not None and return_type is None:
            return_type = ReturnType.TENSORS
        if return_type is not None:
            postprocess_params["return_type"] = return_type
        if continue_final_message is not None:
            postprocess_params["continue_final_message"] = continue_final_message
        if clean_up_tokenization_spaces is not None:
            postprocess_params["clean_up_tokenization_spaces"] = clean_up_tokenization_spaces
        if skip_special_tokens is not None:
            postprocess_params["skip_special_tokens"] = skip_special_tokens

        return preprocess_params, forward_kwargs, postprocess_params