def _truncate(
        self,
        processed_features: dict[str, np.ndarray] | BatchFeature,
        max_length: int | None = None,
        pad_to_multiple_of: int | None = None,
        truncation: bool | None = None,
    ):
        """
        Truncate inputs to predefined length or max length in the batch

        Args:
            processed_features(`Union[dict[str, np.ndarray], BatchFeature]`):
                Dictionary of input values (`np.ndarray[float]`) / input vectors (`list[np.ndarray[float]]`) or batch
                of inputs values (`list[np.ndarray[int]]`) / input vectors (`list[np.ndarray[int]]`)
            max_length (`int`, *optional*):
                maximum length of the returned list and optionally padding length (see below)
            pad_to_multiple_of (`int`, *optional*) :
                Integer if set will pad the sequence to a multiple of the provided value. This is especially useful to
                enable the use of Tensor Core on NVIDIA hardware with compute capability `>= 7.5` (Volta), or on TPUs
                which benefit from having sequence lengths be a multiple of 128.
            truncation (`bool`, *optional*):
                Activates truncation to cut input sequences longer than `max_length` to `max_length`.
        """
        if not truncation:
            return processed_features
        elif truncation and max_length is None:
            raise ValueError("When setting ``truncation=True``, make sure that ``max_length`` is defined.")

        required_input = processed_features[self.model_input_names[0]]

        # find `max_length` that fits `pad_to_multiple_of`
        if max_length is not None and pad_to_multiple_of is not None and (max_length % pad_to_multiple_of != 0):
            max_length = ((max_length // pad_to_multiple_of) + 1) * pad_to_multiple_of

        needs_to_be_truncated = len(required_input) > max_length

        if needs_to_be_truncated:
            processed_features[self.model_input_names[0]] = processed_features[self.model_input_names[0]][:max_length]
            if "attention_mask" in processed_features:
                processed_features["attention_mask"] = processed_features["attention_mask"][:max_length]

        return processed_features