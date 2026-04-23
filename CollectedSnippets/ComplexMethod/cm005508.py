def _maybe_initialize_input_ids_for_generation(
        self: "GenerativePreTrainedModel",
        inputs: torch.Tensor | None,
        bos_token_id: torch.Tensor | None,
        model_kwargs: dict[str, torch.Tensor],
    ) -> torch.LongTensor:
        """Initializes input ids for generation, if necessary."""
        if inputs is not None:
            return inputs

        encoder_outputs = model_kwargs.get("encoder_outputs")
        last_hidden_state = getattr(encoder_outputs, "last_hidden_state", None)
        if self.config.is_encoder_decoder and last_hidden_state is not None:
            # make dummy input_ids with value -100, as a sanity check ensuring that they won't be used for encoding
            shape = last_hidden_state.size()[:-1]
            return torch.ones(shape, dtype=torch.long, device=self.device) * -100

        # If there is some tensor in `model_kwargs`, we can infer the batch size from it. This is helpful with
        # soft-prompting or in multimodal implementations built on top of decoder-only language models.
        batch_size = 1
        for value in model_kwargs.values():
            if isinstance(value, torch.Tensor):
                batch_size = value.shape[0]
                break

        if "inputs_embeds" in model_kwargs:
            return torch.ones(
                (batch_size, 0),
                dtype=torch.long,
                # Use the device of the existing tensor to avoid any potential `meta` device isssue, which is likely
                # linked to the offloading behavior (keeping it on meta device). See PR #44848. Previously, it used
                # `self.device`.
                device=self.device if self.device.type != "meta" else model_kwargs["inputs_embeds"].device,
            )

        if bos_token_id is None:
            raise ValueError("`bos_token_id` has to be defined when no `input_ids` are provided.")

        return torch.ones((batch_size, 1), dtype=torch.long, device=self.device) * bos_token_id