def _pad_batched_inputs(self, inputs: dict[str, Tensor | Any], seq_length: int):
        r"""Override to avoid padding error when handling 3d posids."""
        padding_inputs = {
            k: v.tolist() if v is not None and isinstance(v, Tensor) else v
            for k, v in inputs.items()
            if k in self._language_input_names
        }

        position_ids_3d = None
        if isinstance(inputs.get("position_ids"), Tensor) and inputs["position_ids"].dim() == 3:
            position_ids_3d = inputs["position_ids"]
            padding_inputs.pop("position_ids", None)

        if "labels" in padding_inputs:
            padding_inputs["labels"] = [
                labels + [IGNORE_INDEX] * (seq_length - len(labels)) for labels in padding_inputs["labels"]
            ]
        tokenizer = (
            self.processing_class
            if isinstance(self.processing_class, PreTrainedTokenizerBase)
            else getattr(self.processing_class, "tokenizer", self.processing_class)
        )
        padding_side = getattr(tokenizer, "padding_side", "right")
        padding_inputs = tokenizer.pad(
            padding_inputs,
            padding="max_length",
            max_length=seq_length,
            return_tensors="pt",
        ).to(self.args.device)
        inputs.update(padding_inputs)

        if position_ids_3d is not None:
            current_seq_len = position_ids_3d.size(-1)
            if current_seq_len < seq_length:
                pad_len = seq_length - current_seq_len
                if padding_side == "left":
                    position_ids_3d = F.pad(position_ids_3d, (pad_len, 0), value=0)
                else:
                    position_ids_3d = F.pad(position_ids_3d, (0, pad_len), value=0)

            inputs["position_ids"] = position_ids_3d.to(self.args.device)

        return inputs