def _track_num_input_tokens(self, inputs):
        """Count input tokens seen (all or non-padding) and update state."""
        if self.args.include_num_input_tokens_seen == "no":
            return
        main_input_name = getattr(self.model, "main_input_name", "input_ids")
        if main_input_name not in inputs:
            logger.warning(
                "Tried to track the number of tokens seen, however the current model is "
                "not configured properly to know what item is the input. To fix this, add "
                "a `main_input_name` attribute to the model class you are using."
            )
            return

        if self.args.include_num_input_tokens_seen == "non_padding":
            if "attention_mask" in inputs:
                input_tokens = inputs["attention_mask"].sum()
            elif (
                self.processing_class is not None
                and hasattr(self.processing_class, "pad_token_id")
                and self.processing_class.pad_token_id is not None
            ):
                input_tokens = (inputs[main_input_name] != self.processing_class.pad_token_id).sum()
            else:
                logger.warning(
                    "Could not determine method to count non-padding tokens, falling back to counting all tokens."
                )
                input_tokens = inputs[main_input_name].numel()
        else:
            input_tokens = inputs[main_input_name].numel()

        input_tokens = torch.as_tensor(input_tokens, device=self.args.device, dtype=torch.int64)
        self.state.num_input_tokens_seen += self.accelerator.gather(input_tokens).sum().item()