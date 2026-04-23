def _pad(
        self,
        processed_features: dict[str, np.ndarray] | BatchFeature,
        max_length: int | None = None,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        pad_to_multiple_of: int | None = None,
        return_attention_mask: bool | None = None,
    ) -> dict:
        """
        Pad inputs (on left/right and up to predefined length or max length in the batch)

        Args:
            processed_features (`Union[dict[str, np.ndarray], BatchFeature]`):
                Dictionary of input values (`np.ndarray[float]`) / input vectors (`list[np.ndarray[float]]`) or batch
                of inputs values (`list[np.ndarray[int]]`) / input vectors (`list[np.ndarray[int]]`)
            max_length (`int`, *optional*):
                Maximum length of the returned list and optionally padding length (see below)
            padding_strategy (`PaddingStrategy`, *optional*, default to `PaddingStrategy.DO_NOT_PAD`):
                PaddingStrategy to use for padding.

                - PaddingStrategy.LONGEST Pad to the longest sequence in the batch
                - PaddingStrategy.MAX_LENGTH: Pad to the max length (default)
                - PaddingStrategy.DO_NOT_PAD: Do not pad
                The feature_extractor padding sides are defined in self.padding_side:

                    - 'left': pads on the left of the sequences
                    - 'right': pads on the right of the sequences
            pad_to_multiple_of (`int`, *optional*):
                Integer if set will pad the sequence to a multiple of the provided value. This is especially useful to
                enable the use of Tensor Core on NVIDIA hardware with compute capability `>= 7.5` (Volta), or on TPUs
                which benefit from having sequence lengths be a multiple of 128.
            return_attention_mask (`bool`, *optional*):
                Set to False to avoid returning attention mask (default: set to model specifics)
        """
        required_input = processed_features[self.model_input_names[0]]

        if padding_strategy == PaddingStrategy.LONGEST:
            max_length = len(required_input)

        if max_length is not None and pad_to_multiple_of is not None and (max_length % pad_to_multiple_of != 0):
            max_length = ((max_length // pad_to_multiple_of) + 1) * pad_to_multiple_of

        needs_to_be_padded = padding_strategy != PaddingStrategy.DO_NOT_PAD and len(required_input) < max_length

        if return_attention_mask and "attention_mask" not in processed_features:
            processed_features["attention_mask"] = np.ones(len(required_input), dtype=np.int32)

        if needs_to_be_padded:
            difference = max_length - len(required_input)
            if self.padding_side == "right":
                if return_attention_mask:
                    processed_features["attention_mask"] = np.pad(
                        processed_features["attention_mask"], (0, difference)
                    )
                padding_shape = ((0, difference), (0, 0)) if self.feature_size > 1 else (0, difference)
                processed_features[self.model_input_names[0]] = np.pad(
                    required_input, padding_shape, "constant", constant_values=self.padding_value
                )
            elif self.padding_side == "left":
                if return_attention_mask:
                    processed_features["attention_mask"] = np.pad(
                        processed_features["attention_mask"], (difference, 0)
                    )
                padding_shape = ((difference, 0), (0, 0)) if self.feature_size > 1 else (difference, 0)
                processed_features[self.model_input_names[0]] = np.pad(
                    required_input, padding_shape, "constant", constant_values=self.padding_value
                )
            else:
                raise ValueError("Invalid padding strategy:" + str(self.padding_side))

        return processed_features