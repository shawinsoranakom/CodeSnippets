def generate(
        self,
        coarse_output: torch.Tensor,
        semantic_generation_config: BarkSemanticGenerationConfig | None = None,
        coarse_generation_config: BarkCoarseGenerationConfig | None = None,
        fine_generation_config: BarkFineGenerationConfig = None,
        codebook_size: int = 1024,
        history_prompt: dict[str, torch.Tensor] | None = None,
        **kwargs,
    ) -> torch.LongTensor:
        """
        Generates fine acoustics tokens from input coarse acoustics tokens and an additional optional `Bark` speaker
        prompt.

        Args:
            coarse_output (`torch.Tensor` of shape (batch_size, seq_len)):
                Input coarse acoustics ids, i.e the output of `BarkCoarseModel.generate`.
            semantic_generation_config (`BarkSemanticGenerationConfig`):
                Generation config indicating how to generate the semantic tokens.
            coarse_generation_config (`BarkCoarseGenerationConfig`):
                Generation config indicating how to generate the coarse tokens.
            fine_generation_config (`BarkFineGenerationConfig`):
                Generation config indicating how to generate the fine tokens.
            codebook_size (`int`, *optional*, defaults to 1024):
                Codebook channel size, i.e. the size of the output vocabulary per codebook channel.
            history_prompt (`Optional[dict[str,torch.Tensor]]`, *optional*):
                Optional `Bark` speaker prompt.
        Returns:
            torch.LongTensor: Output fine acoustics tokens.
        """
        if semantic_generation_config is None:
            raise ValueError("`semantic_generation_config` has to be provided")

        if coarse_generation_config is None:
            raise ValueError("`coarse_generation_config` has to be provided")

        if fine_generation_config is None:
            raise ValueError("`fine_generation_config` has to be provided")

        # since we don't really use GenerationConfig through the fine model (autoencoder)
        # and since only temperature is used from the classic GenerationConfig parameters
        # manually impose the kwargs priority over the generation config
        temperature = kwargs.get("temperature", fine_generation_config.temperature)

        max_fine_history_length = fine_generation_config.max_fine_history_length
        max_fine_input_length = fine_generation_config.max_fine_input_length

        # shape: (batch, n_coarse_codebooks * seq_len)
        # new_shape: (batch, seq_len, n_coarse_codebooks)
        coarse_output = coarse_output.view(coarse_output.shape[0], -1, coarse_generation_config.n_coarse_codebooks)

        # brings ids into the range [0, codebook_size -1]
        coarse_output = torch.remainder(coarse_output - semantic_generation_config.semantic_vocab_size, codebook_size)
        batch_size = coarse_output.shape[0]

        if history_prompt is not None:
            x_fine_history = torch.repeat_interleave(history_prompt["fine_prompt"].T[None], batch_size, dim=0)
            # transpose to get to shape (seq_len, n_fine_codebooks)
        else:
            x_fine_history = None

        n_coarse = coarse_generation_config.n_coarse_codebooks

        # pad the last 6th codebooks
        fine_input = F.pad(
            coarse_output,
            (0, fine_generation_config.n_fine_codebooks - n_coarse),
            "constant",
            codebook_size,
        )

        # prepend history if available (max max_fine_history_length)
        if x_fine_history is not None:
            fine_input = torch.cat([x_fine_history[:, -max_fine_history_length:, :], fine_input], dim=1)

            # len of the fine_history that has been added to fine_input
            n_history = x_fine_history[:, -max_fine_history_length:, :].shape[1]
        else:
            n_history = 0

        n_remove_from_end = 0
        # need to pad if too short (since non-causal model)
        if fine_input.shape[1] < max_fine_input_length:
            n_remove_from_end = max_fine_input_length - fine_input.shape[1]
            fine_input = F.pad(fine_input, (0, 0, 0, n_remove_from_end), mode="constant", value=codebook_size)

        # we can be lazy about fractional loop and just keep overwriting codebooks.
        # seems that coarse_output.shape[1] - (max_fine_input_length - n_history) is equal to minus n_remove_from_end
        # So if we needed to pad because too short, n_loops is always 1 (because n_remove_from_end > 0)
        # If not, we loop over at least twice.

        n_loops = (coarse_output.shape[1] - (max_fine_input_length - n_history)) / max_fine_history_length
        n_loops = int(np.ceil(n_loops))
        n_loops = max(0, n_loops) + 1

        for n_outer in range(n_loops):
            start_idx = min([n_outer * max_fine_history_length, fine_input.shape[1] - max_fine_input_length])

            start_fill_idx = min(
                [n_history + n_outer * max_fine_history_length, fine_input.shape[1] - max_fine_history_length]
            )
            rel_start_fill_idx = start_fill_idx - start_idx
            input_buffer = fine_input[:, start_idx : start_idx + max_fine_input_length, :]
            for n_inner in range(n_coarse, fine_generation_config.n_fine_codebooks):
                logits = self.forward(n_inner, input_buffer).logits
                if temperature is None or temperature == 1.0:
                    relevant_logits = logits[:, rel_start_fill_idx:, :codebook_size]
                    codebook_preds = torch.argmax(relevant_logits, -1)
                else:
                    relevant_logits = logits[:, :, :codebook_size] / temperature
                    # apply softmax
                    probs = F.softmax(relevant_logits, dim=-1)[:, rel_start_fill_idx:max_fine_input_length]
                    # reshape to 2D: (batch_size, seq_len, codebook_size) -> (batch_size*seq_len, codebook_size)
                    probs = probs.reshape((-1, codebook_size))
                    # multinomial then reshape : (batch_size*seq_len)-> (batch_size,seq_len)
                    codebook_preds = torch.multinomial(probs, num_samples=1).view(batch_size, -1)
                codebook_preds = codebook_preds.to(torch.int32)
                input_buffer[:, rel_start_fill_idx:, n_inner] = codebook_preds
                del logits, codebook_preds

            # transfer into fine_input
            for n_inner in range(n_coarse, fine_generation_config.n_fine_codebooks):
                fine_input[
                    :, start_fill_idx : start_fill_idx + (max_fine_input_length - rel_start_fill_idx), n_inner
                ] = input_buffer[:, rel_start_fill_idx:, n_inner]
            del input_buffer

        fine_input = fine_input.transpose(1, 2)[:, :, n_history:]
        if n_remove_from_end > 0:
            fine_input = fine_input[:, :, :-n_remove_from_end]

        if fine_input.shape[-1] != coarse_output.shape[-2]:
            raise ValueError("input and output should have the same seq_len")

        return fine_input