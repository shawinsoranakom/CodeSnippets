def _sanitize_parameters(
        self,
        chunk_length_s=None,
        stride_length_s=None,
        ignore_warning=None,
        decoder_kwargs=None,
        return_timestamps=None,
        return_language=None,
        **generate_kwargs,
    ):
        preprocess_params = {}
        forward_params = {}
        postprocess_params = {}

        # Preprocess params
        if chunk_length_s is not None:
            if self.type in ["seq2seq", "seq2seq_whisper"] and not ignore_warning:
                type_warning = (
                    "Using `chunk_length_s` is very experimental with seq2seq models. The results will not necessarily"
                    " be entirely accurate and will have caveats. More information:"
                    " https://github.com/huggingface/transformers/pull/20104. Ignore this warning with pipeline(...,"
                    " ignore_warning=True)."
                )
                if self.type == "seq2seq_whisper":
                    type_warning += (
                        " To use Whisper for long-form transcription, use rather the model's `generate` method directly "
                        "as the model relies on it's own chunking mechanism (cf. Whisper original paper, section 3.8. "
                        "Long-form Transcription)."
                    )
                logger.warning(type_warning)
            preprocess_params["chunk_length_s"] = chunk_length_s
        if stride_length_s is not None:
            preprocess_params["stride_length_s"] = stride_length_s

        # Forward params
        # BC: accept a dictionary of generation kwargs (as opposed to **generate_kwargs)
        if "generate_kwargs" in generate_kwargs:
            forward_params.update(generate_kwargs.pop("generate_kwargs"))
        # Default use for kwargs: they are generation-time kwargs
        forward_params.update(generate_kwargs)

        if getattr(self, "assistant_model", None) is not None:
            forward_params["assistant_model"] = self.assistant_model
        if getattr(self, "assistant_tokenizer", None) is not None:
            forward_params["tokenizer"] = self.tokenizer
            forward_params["assistant_tokenizer"] = self.assistant_tokenizer

        # Postprocess params
        if decoder_kwargs is not None:
            postprocess_params["decoder_kwargs"] = decoder_kwargs
        if return_language is not None:
            if self.type != "seq2seq_whisper":
                raise ValueError("Only Whisper can return language for now.")
            postprocess_params["return_language"] = return_language

        # Parameter used in more than one place
        # in some models like whisper, the generation config has a `return_timestamps` key
        if hasattr(self, "generation_config") and hasattr(self.generation_config, "return_timestamps"):
            return_timestamps = return_timestamps or self.generation_config.return_timestamps

        if return_timestamps is not None:
            # Check whether we have a valid setting for return_timestamps and throw an error before we perform a forward pass
            if self.type == "seq2seq" and return_timestamps:
                raise ValueError("We cannot return_timestamps yet on non-CTC models apart from Whisper!")
            if self.type == "ctc_with_lm" and return_timestamps != "word":
                raise ValueError("CTC with LM can only predict word level timestamps, set `return_timestamps='word'`")
            if self.type == "ctc" and return_timestamps not in ["char", "word"]:
                raise ValueError(
                    "CTC can either predict character level timestamps, or word level timestamps. "
                    "Set `return_timestamps='char'` or `return_timestamps='word'` as required."
                )
            if self.type == "seq2seq_whisper" and return_timestamps == "char":
                raise ValueError(
                    "Whisper cannot return `char` timestamps, only word level or segment level timestamps. "
                    "Use `return_timestamps='word'` or `return_timestamps=True` respectively."
                )
            forward_params["return_timestamps"] = return_timestamps
            postprocess_params["return_timestamps"] = return_timestamps

        return preprocess_params, forward_params, postprocess_params