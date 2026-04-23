def forward(
        self, model: "PreTrainedModel", batch: dict[str, "torch.Tensor"], prefix: Literal["", "kl_"] = ""
    ) -> tuple["torch.Tensor", "torch.Tensor", "torch.Tensor"]:
        r"""Run forward pass and computes the log probabilities."""
        batch = nested_detach(batch, clone=True)  # avoid error
        model_inputs = {
            "input_ids": batch[f"{prefix}input_ids"],
            "attention_mask": batch[f"{prefix}attention_mask"],
        }
        if f"{prefix}token_type_ids" in batch:
            model_inputs["token_type_ids"] = batch[f"{prefix}token_type_ids"]

        if "pixel_values" in batch:
            model_inputs["pixel_values"] = batch["pixel_values"]

        if "image_sizes" in batch:
            model_inputs["image_sizes"] = batch["image_sizes"]

        if "image_grid_thw" in batch:
            model_inputs["image_grid_thw"] = batch["image_grid_thw"]

        if "aspect_ratio_ids" in batch:
            model_inputs["aspect_ratio_ids"] = batch["aspect_ratio_ids"]

        if "aspect_ratio_mask" in batch:
            model_inputs["aspect_ratio_mask"] = batch["aspect_ratio_mask"]

        if f"{prefix}cross_attention_mask" in batch:
            model_inputs["cross_attention_mask"] = batch[f"{prefix}cross_attention_mask"]

        logits = model(**model_inputs, return_dict=True, use_cache=False).logits.to(torch.float32)
        logps, valid_length = get_batch_logps(logits=logits, labels=batch[f"{prefix}labels"])
        return logits, logps, logps / valid_length