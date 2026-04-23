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
        generation_mode=None,
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
        forward_kwargs["generate_kwargs"] = generate_kwargs or {}
        if generation_mode is not None and generation_mode != "text":
            forward_kwargs["generate_kwargs"]["generation_mode"] = generation_mode
        # Qwen-Omni models need to know the origin of audio, to align mm position ids
        if kwargs.get("load_audio_from_video") and re.search(r"qwen\domni", self.model.__class__.__name__.lower()):
            forward_kwargs["generate_kwargs"]["use_audio_in_video"] = True
        if stop_sequence is not None:
            if isinstance(stop_sequence, str):
                stop_sequence = [stop_sequence]
            forward_kwargs["generate_kwargs"]["stop_strings"] = stop_sequence
            forward_kwargs["generate_kwargs"]["tokenizer"] = self.processor.tokenizer

        if max_new_tokens is not None:
            if generate_kwargs is not None and "max_new_tokens" in generate_kwargs:
                raise ValueError(
                    "'max_new_tokens' is defined twice, once in 'generate_kwargs' and "
                    "once as a direct argument. Please use only one."
                )
            forward_kwargs["generate_kwargs"]["max_new_tokens"] = max_new_tokens

        if return_full_text is not None and return_type is None:
            if return_tensors is not None:
                raise ValueError("`return_full_text` is mutually exclusive with `return_tensors`")
            return_type = ReturnType.FULL_TEXT if return_full_text else ReturnType.NEW_TEXT
        elif return_tensors is not None and return_type is None:
            return_type = ReturnType.TENSORS
        # We don't want to set the global default to FULLTEXT at init time. That is why
        # `_postprocess_params` is checked before setting the default value
        elif return_type is None and generation_mode in [None, "text"] and hasattr(self, "_postprocess_params"):
            return_type = ReturnType.FULL_TEXT

        # Postprocess params
        if generation_mode not in [None, "text"] and return_type is not None:
            raise ValueError(
                f"`return_type` cannot be set to {return_type} when generation_mode={generation_mode}. "
                "Set `return_type=None` or generation_mode='text'"
            )
        if generation_mode not in [None, "text", "image", "audio"]:
            raise ValueError(
                f"`generation_mode` can be only one of the `text`, `audio`, `image` but got generation_mode[={generation_mode}]"
            )
        elif generation_mode is not None and generation_mode not in self.model.output_modalities:
            raise ValueError(
                f"`generation_mode={generation_mode}` is not supported for {self.model.__class__.__name__}. "
                f"The model can only output the following modalities: {self.model.output_modalities}"
            )

        if return_type is not None:
            postprocess_params["return_type"] = return_type
        if continue_final_message is not None:
            postprocess_params["continue_final_message"] = continue_final_message
        if clean_up_tokenization_spaces is not None:
            postprocess_params["clean_up_tokenization_spaces"] = clean_up_tokenization_spaces
        if skip_special_tokens is not None:
            postprocess_params["skip_special_tokens"] = skip_special_tokens
        postprocess_params["generation_mode"] = generation_mode
        return preprocess_params, forward_kwargs, postprocess_params