def _parse_and_validate_audio_input(
        self,
        **kwargs: object,
    ) -> GraniteSpeechAudioInputs | None:
        input_features = kwargs.pop("input_features", None)
        input_features_mask = kwargs.pop("input_features_mask", None)
        audio_embed_sizes = kwargs.pop("audio_embed_sizes", None)

        if input_features is None:
            return None

        # If we have a batch of variable feature length audio clips, we need
        # to mask the features; usually we would get an input_features_mask
        # from the processor, but we handle rebuilding it here since
        # vLLM generally processes everything independently + batches.
        if input_features_mask is None:
            input_features_mask = self._build_input_features_mask(audio_embed_sizes)

        if not isinstance(input_features, (torch.Tensor, list)):
            raise ValueError(
                "Incorrect type of audio input features. "
                f"Got type: {type(input_features)}"
            )

        if input_features_mask is not None and not isinstance(
            input_features_mask, torch.Tensor
        ):
            raise ValueError(
                "Incorrect type of audio input features mask. "
                f"Got type: {type(input_features_mask)}"
            )

        if isinstance(input_features, torch.Tensor):
            # Granite speech currently only allows one audio token per instance
            # and features are already unsqueezed in the processor, so one
            # instance will have shape [1, {num_features}, 160]. As such,
            # input features will usually be of shape
            # [bsz, 1, num_features, 160], which we squeeze to be 3D here.
            if len(input_features.shape) == 4:
                input_features = input_features.squeeze(1)
            if len(input_features.shape) != 3:
                raise ValueError(
                    "Squeezed input features should be 3D but are of shape "
                    f"{input_features.shape}"
                )
            input_features = input_features.to(self.encoder.input_linear.weight.dtype)

        else:
            # Otherwise we have a list of tensors, which are almost certainly
            # differing in their respective numbers of audio features; when
            # passed as a batch, we expect a list of 2D var len input features
            # so unsqueeze them.
            input_features = [
                feat.unsqueeze(dim=0) for feat in input_features if feat.ndim == 2
            ]

            # stack them into a 3D tensor of size [bsz, most_num_features, 160].
            input_features = self._pad_and_stack_input_features(
                input_features,
            ).to(self.encoder.input_linear.weight.dtype)

        return GraniteSpeechAudioInputs(
            input_features=input_features,
            input_features_mask=input_features_mask,
            audio_embed_sizes=audio_embed_sizes.flatten().tolist(),
        )