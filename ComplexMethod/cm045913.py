def generate_export(
            self,
            encoder_outputs,
            model_kwargs,
    ):
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
        if not use_parallel:
            input_ids = input_ids.reshape([-1, 1])
        decoder_input_ids = input_ids
        model_kwargs["key use_cache"] = True
        batch_size, cur_len = input_ids.shape

        if "inputs_embeds" in model_kwargs:
            cur_len = model_kwargs["inputs_embeds"].shape[1]

        cache_position = torch.arange(cur_len)
        pad_token_id = self.pad_token_id
        eos_token_id = [self.eos_token_id]
        eos_token = self.eos_token_id
        if use_parallel:
            unfinished_sequences = torch.ones(
                [batch_size, parallel_step], dtype=torch.int64, device=self.device
            )
            parallel_length = math.ceil(self.max_seq_len // parallel_step)
        else:
            unfinished_sequences = torch.ones(batch_size, dtype=torch.int64, device=self.device)
            parallel_length = self.max_seq_len

        i_idx = 0
        past_key_values = []
        decoder_attention_heads = self.config_decoder.decoder_attention_heads
        decoder_attention_heads_dim = int(
            self.config_decoder.d_model / decoder_attention_heads
        )
        for i in range(self.config_decoder.decoder_layers):
            init_arr = torch.zeros(
                [batch_size, decoder_attention_heads, 0, decoder_attention_heads_dim]
            )
            cache = (init_arr, init_arr, init_arr, init_arr)
            past_key_values.append(cache)

        while i_idx < parallel_length:

            model_inputs = self.prepare_inputs_for_generation_export(
                past_key_values=past_key_values, **model_kwargs
            )
            decoder_attention_mask = torch.ones(input_ids.shape, device=self.device)

            outputs = self.generate_single_iter(
                decoder_input_ids=decoder_input_ids,
                decoder_attention_mask=decoder_attention_mask,
                encoder_outputs=encoder_outputs,
                past_key_values=past_key_values,
                return_dict=True,
                output_attentions=False,
                output_hidden_states=False,
            )

            if use_parallel:
                next_token_logits = outputs.logits[:, -parallel_step:, :]
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
                decoder_input_ids = next_tokens
            else:
                input_ids = torch.concat(
                    [input_ids, next_tokens.unsqueeze(1)], dim=-1
                )
                decoder_input_ids = next_tokens.unsqueeze(1)

            past_length = past_key_values[0][0].shape[2]

            past_key_values = outputs.past_key_values
            cache_position = cache_position[-1:] + 1
            if use_parallel:
                unfinished_sequences = (
                        unfinished_sequences
                        & ~self.stopping_criteria_parallel(input_ids).to(torch.int64).to(self.device)
                )
            else:
                unfinished_sequences = unfinished_sequences & ~self.stopping_criteria(
                    input_ids
                ).to(torch.int64).to(self.device)

            if (
                    eos_token is not None
                    and (
                    torch.cumsum((input_ids == eos_token).to(torch.int64), 1)[:, -1]
                    >= 1
            ).all()
            ):
                break
            i_idx += 1
            # break

        return input_ids