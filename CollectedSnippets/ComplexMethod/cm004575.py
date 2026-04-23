def _prepare_decoder_input_ids_for_generation(
        self,
        batch_size: int,
        model_input_name: str,
        model_kwargs: dict[str, torch.Tensor],
        decoder_start_token_id: torch.Tensor,
        device: torch.device | None = None,
    ) -> tuple[torch.LongTensor, dict[str, torch.Tensor]]:
        """Prepares `decoder_input_ids` for generation with encoder-decoder models"""
        # 1. Check whether the user has defined `decoder_input_ids` and `decoder_attention_mask`; if not error out
        decoder_input_ids = decoder_attention_mask = None
        if model_kwargs is not None and "decoder_input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("decoder_input_ids")
        if model_kwargs is not None and "decoder_attention_mask" in model_kwargs:
            decoder_attention_mask = model_kwargs.pop("decoder_attention_mask")

        # We allow generating without preparation (no proper delay) but discourage it
        if decoder_input_ids is None or decoder_attention_mask is None:
            logger.warning_once(
                "In order to generate with Dia, we need the processed audio input: Got `decoder_input_ids`:"
                f" {decoder_input_ids is not None} and got `decoder_attention_mask`={decoder_attention_mask is not None}."
                f" This can be achieved via the [`DiaProcessor`] but now defaulting to non-delayed generation."
            )

            num_channels = self.config.decoder_config.num_channels
            real_batch_size = batch_size // 2 if self._uses_cfg else batch_size

            if decoder_input_ids is None:
                decoder_input_ids = torch.full(
                    (real_batch_size, 1, num_channels), decoder_start_token_id, dtype=torch.long, device=device
                )

            decoder_attention_mask = torch.ones(
                size=(real_batch_size, decoder_input_ids.shape[1]), dtype=torch.long, device=device
            )

        # 2. Determine the valid input and what works as mask within the input
        delay_mask = decoder_input_ids.long()
        valid_input_size = (
            decoder_input_ids.shape[1]
            - (decoder_input_ids[:, :, 0] == self.config.decoder_config.pad_token_id).sum(dim=-1).max()
        )
        decoder_input_ids = delay_mask[:, :valid_input_size].transpose(1, 2).long()
        decoder_attention_mask = decoder_attention_mask[:, :valid_input_size].long()

        # 3. Overwrite into model kwargs
        model_kwargs["decoder_attention_mask"] = decoder_attention_mask
        model_kwargs["decoder_delay_mask"] = delay_mask

        return decoder_input_ids, model_kwargs