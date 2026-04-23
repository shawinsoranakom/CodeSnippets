def _prepare_special_tokens(
        self: "GenerativePreTrainedModel",
        generation_config: GenerationConfig,
        kwargs_has_attention_mask: bool | None = None,
        device: torch.device | str | None = None,
    ):
        """
        Prepares the special tokens for generation, overwriting the generation config with their processed versions
        converted to tensor.

        Note that `generation_config` is changed in place and stops being serializable after this method is called.
        That is no problem if called within `generate` (`generation_config` is a local copy that doesn't leave the
        function). However, if called outside `generate`, consider creating a copy of `generation_config` first.
        """

        # Convert special tokens to tensors
        def _tensor_or_none(token, device=None):
            if token is None:
                return token

            device = device if device is not None else self.device
            if isinstance(token, torch.Tensor):
                return token.to(device)
            return torch.tensor(token, device=device, dtype=torch.long)

        bos_token_tensor = _tensor_or_none(generation_config.bos_token_id, device=device)
        eos_token_tensor = _tensor_or_none(generation_config.eos_token_id, device=device)
        pad_token_tensor = _tensor_or_none(generation_config.pad_token_id, device=device)
        decoder_start_token_tensor = _tensor_or_none(generation_config.decoder_start_token_id, device=device)

        # for BC we also try to get `decoder_start_token_id` or `bos_token_id` (#30892)
        if self.config.is_encoder_decoder:
            decoder_start_token_tensor = (
                decoder_start_token_tensor if decoder_start_token_tensor is not None else bos_token_tensor
            )

        # We can have more than one eos token. Always treat it as a 1D tensor (when it exists).
        if eos_token_tensor is not None and eos_token_tensor.ndim == 0:
            eos_token_tensor = eos_token_tensor.unsqueeze(0)

        # Set pad token if unset (and there are conditions to do so)
        if pad_token_tensor is None and eos_token_tensor is not None:
            if kwargs_has_attention_mask is not None and not kwargs_has_attention_mask:
                logger.warning(
                    "The attention mask and the pad token id were not set. As a consequence, you may observe "
                    "unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results."
                )
            pad_token_tensor = eos_token_tensor[0]
            logger.warning(f"Setting `pad_token_id` to `eos_token_id`:{pad_token_tensor} for open-end generation.")

        # Sanity checks/warnings
        if self.config.is_encoder_decoder and decoder_start_token_tensor is None:
            raise ValueError(
                "`decoder_start_token_id` or `bos_token_id` has to be defined for encoder-decoder generation."
            )
        if eos_token_tensor is not None and torch.isin(eos_token_tensor, pad_token_tensor).any():
            if kwargs_has_attention_mask is not None and not kwargs_has_attention_mask:
                logger.warning_once(
                    "The attention mask is not set and cannot be inferred from input because pad token is same as "
                    "eos token. As a consequence, you may observe unexpected behavior. Please pass your input's "
                    "`attention_mask` to obtain reliable results."
                )
        if eos_token_tensor is not None and (
            torch.is_floating_point(eos_token_tensor) or (eos_token_tensor < 0).any()
        ):
            logger.warning(
                f"`eos_token_id` should consist of positive integers, but is {eos_token_tensor}. Your generation "
                "will not stop until the maximum length is reached. Depending on other flags, it may even crash."
            )

        # Update generation config with the updated special tokens tensors
        # NOTE: this must be written into a different attribute name than the one holding the original special tokens
        # (in their non-tensor form), in order to enable end-to-end compilation. See
        # https://pytorch.org/docs/stable/torch.compiler_cudagraph_trees.html#limitations
        generation_config._bos_token_tensor = bos_token_tensor
        generation_config._eos_token_tensor = eos_token_tensor
        generation_config._pad_token_tensor = pad_token_tensor
        generation_config._decoder_start_token_tensor = decoder_start_token_tensor