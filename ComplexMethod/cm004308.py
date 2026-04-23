def _pad(
        self,
        encoded_inputs: dict[str, EncodedInput] | BatchEncoding,
        max_length: int | None = None,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_attention_mask: bool | None = None,
    ) -> dict:
        """
        Pad encoded inputs (on left/right and up to predefined length or max length in the batch)

        Args:
            encoded_inputs:
                Dictionary of tokenized inputs (`list[int]`) or batch of tokenized inputs (`list[list[int]]`).
            max_length: maximum length of the returned list and optionally padding length (see below).
                Will truncate by taking into account the special tokens.
            padding_strategy: PaddingStrategy to use for padding.

                - PaddingStrategy.LONGEST Pad to the longest sequence in the batch
                - PaddingStrategy.MAX_LENGTH: Pad to the max length (default)
                - PaddingStrategy.DO_NOT_PAD: Do not pad
                The tokenizer padding sides are defined in self.padding_side:

                    - 'left': pads on the left of the sequences
                    - 'right': pads on the right of the sequences
            pad_to_multiple_of: (optional) Integer if set will pad the sequence to a multiple of the provided value.
                This is especially useful to enable the use of Tensor Core on NVIDIA hardware with compute capability
                `>= 7.5` (Volta).
            padding_side:
                The side on which the model should have padding applied. Should be selected between ['right', 'left'].
                Default value is picked from the class attribute of the same name.
            return_attention_mask:
                (optional) Set to False to avoid returning attention mask (default: set to model specifics)
        """
        # Load from model defaults
        if return_attention_mask is None:
            return_attention_mask = "attention_mask" in self.model_input_names

        if padding_strategy == PaddingStrategy.LONGEST:
            max_length = len(encoded_inputs["input_ids"])

        if max_length is not None and pad_to_multiple_of is not None and (max_length % pad_to_multiple_of != 0):
            max_length = ((max_length // pad_to_multiple_of) + 1) * pad_to_multiple_of

        needs_to_be_padded = (
            padding_strategy != PaddingStrategy.DO_NOT_PAD and len(encoded_inputs["input_ids"]) != max_length
        )

        # Initialize attention mask if not present.
        if return_attention_mask and "attention_mask" not in encoded_inputs:
            encoded_inputs["attention_mask"] = [1] * len(encoded_inputs["input_ids"])

        if needs_to_be_padded:
            difference = max_length - len(encoded_inputs["input_ids"])
            padding_side = padding_side if padding_side is not None else self.padding_side
            if padding_side == "right":
                if return_attention_mask:
                    encoded_inputs["attention_mask"] = encoded_inputs["attention_mask"] + [0] * difference
                if "token_type_ids" in encoded_inputs:
                    encoded_inputs["token_type_ids"] = (
                        encoded_inputs["token_type_ids"] + [[self.pad_token_type_id] * 7] * difference
                    )
                if "labels" in encoded_inputs:
                    encoded_inputs["labels"] = encoded_inputs["labels"] + [0] * difference
                if "numeric_values" in encoded_inputs:
                    encoded_inputs["numeric_values"] = encoded_inputs["numeric_values"] + [float("nan")] * difference
                if "numeric_values_scale" in encoded_inputs:
                    encoded_inputs["numeric_values_scale"] = (
                        encoded_inputs["numeric_values_scale"] + [1.0] * difference
                    )
                if "special_tokens_mask" in encoded_inputs:
                    encoded_inputs["special_tokens_mask"] = encoded_inputs["special_tokens_mask"] + [1] * difference
                encoded_inputs["input_ids"] = encoded_inputs["input_ids"] + [self.pad_token_id] * difference
            elif padding_side == "left":
                if return_attention_mask:
                    encoded_inputs["attention_mask"] = [0] * difference + encoded_inputs["attention_mask"]
                if "token_type_ids" in encoded_inputs:
                    encoded_inputs["token_type_ids"] = [[self.pad_token_type_id] * 7] * difference + encoded_inputs[
                        "token_type_ids"
                    ]
                if "labels" in encoded_inputs:
                    encoded_inputs["labels"] = [0] * difference + encoded_inputs["labels"]
                if "numeric_values" in encoded_inputs:
                    encoded_inputs["numeric_values"] = [float("nan")] * difference + encoded_inputs["numeric_values"]
                if "numeric_values_scale" in encoded_inputs:
                    encoded_inputs["numeric_values_scale"] = [1.0] * difference + encoded_inputs[
                        "numeric_values_scale"
                    ]
                if "special_tokens_mask" in encoded_inputs:
                    encoded_inputs["special_tokens_mask"] = [1] * difference + encoded_inputs["special_tokens_mask"]
                encoded_inputs["input_ids"] = [self.pad_token_id] * difference + encoded_inputs["input_ids"]
            else:
                raise ValueError("Invalid padding strategy:" + str(padding_side))

        return encoded_inputs