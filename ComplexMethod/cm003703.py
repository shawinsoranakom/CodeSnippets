def _prepare_model_inputs(
        self,
        inputs: torch.Tensor | None,
        bos_token_id: int | None,
        model_kwargs: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, str | None, dict[str, torch.Tensor]]:
        """
        This function extracts the model-specific `inputs` for generation.
        """
        input_name = self.main_input_name

        model_kwargs = {k: v for k, v in model_kwargs.items() if v is not None}

        inputs_kwarg = model_kwargs.pop(input_name, None)
        if inputs_kwarg is not None and inputs is not None:
            raise ValueError(
                f"`inputs`: {inputs}` were passed alongside {input_name} which is not allowed."
                f"Make sure to either pass {inputs} or {input_name}=..."
            )
        elif inputs_kwarg is not None:
            inputs = inputs_kwarg

        if input_name == "input_ids" and "inputs_embeds" in model_kwargs:
            model_kwargs["input_ids"] = self._maybe_initialize_input_ids_for_generation(
                inputs, bos_token_id, model_kwargs=model_kwargs
            )
            inputs, input_name = model_kwargs["inputs_embeds"], "inputs_embeds"

        # Check if conditioning_embeds are provided or not, if yes then concatenate the bos_token_id at the end of the conditioning_embeds.
        # Then we must subtract the positional_ids because during the forward pass it will be added anyways, so we must cancel them out here.
        conditioning_embeds = model_kwargs.get("conditioning_embeds")

        if conditioning_embeds is not None:
            mel_start_token_embedding = self.model.decoder.input_embeds_layer(
                torch.full(
                    (conditioning_embeds.shape[0], 1),
                    fill_value=self.config.bos_token_id,
                    device=conditioning_embeds.device,
                )
            )
            mel_start_token_embedding += self.model.decoder.position_embeds_layer(
                torch.full((conditioning_embeds.shape[0], 1), fill_value=0, device=conditioning_embeds.device)
            )
            conditioning_embeds = torch.concat([conditioning_embeds, mel_start_token_embedding], dim=1)

            # subtract the positional_ids here
            if hasattr(model_kwargs, "attention_mask"):
                position_ids = model_kwargs["attention_mask"].long().cumsum(-1) - 1
            else:
                position_ids = torch.arange(
                    0, conditioning_embeds.shape[1], dtype=torch.long, device=conditioning_embeds.device
                )
            position_ids = position_ids.unsqueeze(0).repeat(conditioning_embeds.shape[0], 1)

            model_kwargs["inputs_embeds"] = conditioning_embeds - self.model.decoder.position_embeds_layer(
                position_ids
            )
            model_kwargs["input_ids"] = (
                torch.ones((model_kwargs["inputs_embeds"].shape[0], 1), dtype=torch.long, device=self.device)
                * self.config.bos_token_id
            )

            return model_kwargs["inputs_embeds"], "inputs_embeds", model_kwargs

        inputs = self._maybe_initialize_input_ids_for_generation(inputs, bos_token_id, model_kwargs)
        return inputs, input_name, model_kwargs