def _prepare_decoder_input_ids_for_generation(
        self: "GenerativePreTrainedModel",
        batch_size: int,
        model_input_name: str,
        model_kwargs: dict[str, torch.Tensor],
        decoder_start_token_id: torch.Tensor,
        device: torch.device | None = None,
    ) -> tuple[torch.LongTensor, dict[str, torch.Tensor]]:
        """Prepares `decoder_input_ids` for generation with encoder-decoder models"""
        # 1. Check whether the user has defined `decoder_input_ids` manually. To facilitate in terms of input naming,
        # we also allow the user to pass it under `input_ids`, if the encoder does not use it as the main input.
        if model_kwargs is not None and "decoder_input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("decoder_input_ids")
        elif "input_ids" in model_kwargs and model_input_name != "input_ids":
            decoder_input_ids = model_kwargs.pop("input_ids")
        else:
            decoder_input_ids = None

        # 2. `decoder_start_token_id` must have shape (batch_size, 1)
        if device is None:
            device = self.device
        if decoder_start_token_id.ndim == 1:
            if decoder_start_token_id.shape[0] != batch_size:
                raise ValueError(
                    f"`decoder_start_token_id` expected to have length {batch_size} but got {decoder_start_token_id.shape[0]}"
                )
            decoder_start_token_id = decoder_start_token_id.view(-1, 1)
        else:
            decoder_start_token_id = (
                torch.ones((batch_size, 1), dtype=torch.long, device=device) * decoder_start_token_id
            )

        # 3. Encoder-decoder models expect the `decoder_input_ids` to start with a special token. Let's ensure that.
        # no user input -> use decoder_start_token_id as decoder_input_ids
        if decoder_input_ids is None:
            decoder_input_ids = decoder_start_token_id
        # exception: Donut checkpoints have task-specific decoder starts and don't expect a BOS token. Note that the
        # original checkpoints can't be detected through `self.__class__.__name__.lower()`, needing custom logic.
        # See: https://github.com/huggingface/transformers/pull/31470
        elif "donut" in self.__class__.__name__.lower() or (
            self.config.model_type == "vision-encoder-decoder" and "donut" in self.config.encoder.model_type.lower()
        ):
            pass
        elif self.config.model_type == "whisper":
            pass
        # user input but doesn't start with decoder_start_token_id -> prepend decoder_start_token_id (and adjust
        # decoder_attention_mask if provided)
        elif (decoder_input_ids[:, 0] != decoder_start_token_id[:, 0]).all().item():
            decoder_input_ids = torch.cat([decoder_start_token_id, decoder_input_ids], dim=-1)
            if "decoder_attention_mask" in model_kwargs:
                decoder_attention_mask = model_kwargs["decoder_attention_mask"]
                decoder_attention_mask = torch.cat(
                    (torch.ones_like(decoder_attention_mask)[:, :1], decoder_attention_mask),
                    dim=-1,
                )
                model_kwargs["decoder_attention_mask"] = decoder_attention_mask

        return decoder_input_ids, model_kwargs