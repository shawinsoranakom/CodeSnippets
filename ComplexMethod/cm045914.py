def generate(
            self,
            encoder_outputs,
            model_kwargs,
    ):
        """
        Generate sequences from the model without computing gradients.

        This method is used to generate sequences from the model based on the given encoder outputs.
        It does not compute gradients, making it suitable for inference.

        Args:
            encoder_outputs: The outputs from the encoder, typically including hidden states necessary for generation.
            model_kwargs: Additional keyword arguments that may include parameters such as maximum length,
                        temperature, top-k/top-p sampling parameters, and other generation-specific settings.

        Returns:
            Generated sequences based on the encoder outputs and specified generation parameters.
        """
        use_parallel = self.config_decoder.use_parallel
        parallel_step = self.config_decoder.parallel_step
        batch_size = encoder_outputs["last_hidden_state"].shape[0]
        generation_config = {
            "decoder_start_token_id": 0,
            "bos_token_id": 0,
        }

        input_ids, model_kwargs = self._prepare_decoder_input_ids_for_generation(
            batch_size=batch_size,
            model_kwargs=model_kwargs,
            decoder_start_token_id=generation_config["decoder_start_token_id"],
            bos_token_id=generation_config["bos_token_id"],
        )

        decoder_input_ids = input_ids
        model_kwargs["key use_cache"] = True
        batch_size, cur_len = input_ids.shape

        if "inputs_embeds" in model_kwargs:
            cur_len = model_kwargs["inputs_embeds"].shape[1]
        model_kwargs["cache_position"] = torch.arange(cur_len)
        pad_token_id = self.pad_token_id
        eos_token_id = [self.eos_token_id]
        eos_token = self.eos_token_id
        if use_parallel:
            unfinished_sequences = torch.ones(
                [batch_size, parallel_step], dtype=torch.int64
            )
            parallel_length = math.ceil(self.max_seq_len // parallel_step)
        else:
            unfinished_sequences = torch.ones(batch_size, dtype=torch.int64)
            parallel_length = self.max_seq_len
        past_key_values = []

        for idx in range(parallel_length):

            model_inputs = self.prepare_inputs_for_generation(input_ids, **model_kwargs)
            outputs = self.generate_single_iter(
                **model_inputs,
                encoder_outputs=encoder_outputs,
                return_dict=True,
                output_attentions=False,
                output_hidden_states=False,
            )

            if use_parallel:
                next_token_logits = outputs.logits[:, :, :]
            else:
                next_token_logits = outputs.logits[:, -1, :]

            next_tokens_scores = self.logits_processor(input_ids, next_token_logits)
            next_tokens = torch.argmax(next_tokens_scores, dim=-1)
            if eos_token_id is not None:
                # False
                if pad_token_id is None:
                    raise ValueError(
                        "If `eos_token_id` is defined, make sure that `pad_token_id` is defined."
                    )
                next_tokens = next_tokens * unfinished_sequences + pad_token_id * (
                        1 - unfinished_sequences
                )
            if use_parallel:
                input_ids = torch.concat([input_ids, next_tokens], dim=-1)
            else:
                input_ids = torch.concat([input_ids, next_tokens[:, None]], dim=-1)

            model_kwargs = self._update_model_kwargs_for_generation(
                outputs,
                model_kwargs,
                is_encoder_decoder=self.config_decoder.is_encoder_decoder,
            )
            if use_parallel:
                unfinished_sequences = (
                        unfinished_sequences
                        & ~self.stopping_criteria_parallel(input_ids).to(torch.int64)
                )
            else:
                unfinished_sequences = unfinished_sequences & ~self.stopping_criteria(
                    input_ids
                ).to(torch.int64)

            if (
                    eos_token is not None
                    and (
                    torch.cumsum((input_ids == eos_token).to(torch.int64), 1)[:, -1]
                    >= 1
            ).all()
            ):
                break
        return input_ids