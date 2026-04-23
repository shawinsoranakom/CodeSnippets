def _check_generate_outputs(self, output, config, use_cache=False, num_return_sequences=1, num_beams=1):
        input_batch_size = int(output.sequences.shape[0] / num_return_sequences)
        internal_batch_size = (
            input_batch_size * num_beams if num_beams > 1 else input_batch_size * num_return_sequences
        )

        prompt_length = getattr(self.model_tester, "seq_length", None)
        prompt_length = getattr(self.model_tester, "encoder_seq_length", prompt_length)
        prompt_length = getattr(self.model_tester, "text_seq_length", prompt_length)

        config = config.text_config if hasattr(config, "text_config") else config

        generated_length = (
            output.sequences.shape[1] - 1 if config.is_encoder_decoder else output.sequences.shape[1] - prompt_length
        )

        cache = getattr(output, "past_key_values", None)
        decoder_past_key_values = cache.self_attention_cache if isinstance(cache, EncoderDecoderCache) else cache

        # in some models we subsample the sequence length in inner layers
        if hasattr(self.model_tester, "get_subsampled_output_lengths"):
            prompt_length = self.model_tester.get_subsampled_output_lengths(prompt_length)

        # scores
        self._check_scores(
            batch_size=internal_batch_size, scores=output.scores, generated_length=generated_length, config=config
        )

        # unprocessed logits
        self._check_logits(batch_size=internal_batch_size, logits=output.logits, config=config)

        # Attentions
        if self.has_attentions:
            if config.is_encoder_decoder:
                # encoder
                self._check_encoder_attention_for_generate(
                    attentions=output.encoder_attentions,
                    batch_size=input_batch_size,
                    config=config,
                    prompt_length=prompt_length,
                )
                # decoder
                self._check_attentions_for_generate(
                    batch_size=internal_batch_size,
                    attentions=output.decoder_attentions,
                    prompt_length=1,  # the BOS token
                    output_length=output.sequences.shape[1],
                    config=config,
                    decoder_past_key_values=decoder_past_key_values,
                )
            else:
                self._check_attentions_for_generate(
                    batch_size=internal_batch_size,
                    attentions=output.attentions,
                    prompt_length=prompt_length,
                    output_length=output.sequences.shape[1],
                    config=config,
                    decoder_past_key_values=decoder_past_key_values,
                )

        # Hidden States
        if config.is_encoder_decoder:
            # encoder
            self._check_encoder_hidden_states_for_generate(
                hidden_states=output.encoder_hidden_states,
                batch_size=input_batch_size,
                config=config,
                prompt_length=prompt_length,
            )
            # decoder
            self._check_hidden_states_for_generate(
                batch_size=internal_batch_size,
                hidden_states=output.decoder_hidden_states,
                prompt_length=1,  # the BOS token
                output_length=output.sequences.shape[1],
                config=config,
                use_cache=use_cache,
            )
        else:
            self._check_hidden_states_for_generate(
                batch_size=internal_batch_size,
                hidden_states=output.hidden_states,
                prompt_length=prompt_length,
                output_length=output.sequences.shape[1],
                config=config,
                use_cache=use_cache,
            )

        # Check the cache shape
        if use_cache:
            cache_length = output.sequences.shape[1] - 1
            self._check_past_key_values_for_generate(
                batch_size=internal_batch_size,
                past_key_values=cache,
                seq_length=cache_length,
                config=config,
            )
        # xlnet has a weird list cache, which is returned even with `use_cache=False`...
        elif "xlnet" not in config.__class__.__name__.lower():
            self.assertTrue(cache is None)