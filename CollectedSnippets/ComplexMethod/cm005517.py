def _validate_generation_mode(
        self: "GenerativePreTrainedModel", generation_mode, generation_config, generation_mode_kwargs
    ):
        if generation_mode == GenerationMode.BEAM_SEARCH and "streamer" in generation_mode_kwargs:
            raise ValueError(
                "`streamer` cannot be used with beam search (yet!). Make sure that `num_beams` is set to 1."
            )

        if generation_mode == GenerationMode.ASSISTED_GENERATION:
            if generation_config.num_return_sequences > 1:
                raise ValueError(
                    "num_return_sequences has to be 1 when doing assisted generate, "
                    f"but is {generation_config.num_return_sequences}."
                )
            if self._is_stateful:
                # In assisted generation we need the ability to confirm whether the model would pick certain tokens,
                # which is not possible with stateful models (they can't reset to a previous subset of generated text)
                raise ValueError(
                    f"assisted generation is not supported with stateful models, such as {self.__class__.__name__}"
                )

        if (assistant_model := generation_mode_kwargs.get("assistant_model")) is not None:
            if self.config.is_encoder_decoder and not assistant_model.config.is_encoder_decoder:
                attributes_to_check = ["encoder_attention_heads", "encoder_ffn_dim", "encoder_layers"]
                attributes_to_check = [attr for attr in dir(assistant_model.config) if attr in attributes_to_check]
                are_equal = all(
                    getattr(self.config, attr) == getattr(assistant_model.config, attr) for attr in attributes_to_check
                )
                if not are_equal:
                    raise ValueError(
                        "The main model and the assistant don't have compatible encoder-dependent input shapes. "
                        "Ensure you load the assistant with the correct encoder-decoder class, e.g. `AutoModelForSpeechSeq2Seq` for Whisper."
                    )

            doc_reference = (
                "(see https://huggingface.co/docs/transformers/en/generation_strategies#universal-assisted-decoding)"
            )
            if self.config.get_text_config().vocab_size == assistant_model.config.get_text_config().vocab_size:
                if "assistant_tokenizer" in generation_mode_kwargs:
                    raise ValueError(
                        f"`assistant_tokenizer` is not required when the main and assistant models use the same tokenizer. Please omit `assistant_tokenizer` from `generate()` {doc_reference}."
                    )
            else:
                if "tokenizer" not in generation_mode_kwargs or "assistant_tokenizer" not in generation_mode_kwargs:
                    raise ValueError(
                        f"The main and assistant models have different tokenizers. Please provide `tokenizer` and `assistant_tokenizer` to `generate()` {doc_reference}."
                    )