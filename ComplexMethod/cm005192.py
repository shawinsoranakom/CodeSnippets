def forward(
        self,
        pixel_values_videos: torch.Tensor | None = None,
        mask_labels: list[torch.Tensor] | None = None,
        class_labels: list[torch.Tensor] | None = None,
        patch_offsets: list[torch.Tensor] | None = None,  # Unused, kept for modular compatibility.
        **kwargs: Unpack[TransformersKwargs],
    ) -> VideomtForUniversalSegmentationOutput:
        r"""
        pixel_values_videos (`torch.Tensor`, *optional*):
            Video inputs of shape `(batch_size, num_frames, num_channels, height, width)`.
        mask_labels (`list[torch.Tensor]`, *optional*):
            Not supported for 5D video inputs.
        class_labels (`list[torch.LongTensor]`, *optional*):
            Not supported for 5D video inputs.
        patch_offsets (`list[torch.Tensor]`, *optional*):
            Unused for video inputs and only kept for modular compatibility.
        """
        if "pixel_values" in kwargs:
            raise ValueError("Use `pixel_values_videos` with `VideomtForUniversalSegmentation`.")

        if pixel_values_videos is None:
            raise ValueError("You have to specify pixel_values_videos")

        if pixel_values_videos.ndim != 5:
            raise ValueError(
                "VideomtForUniversalSegmentation only supports 5D video inputs of shape "
                "(batch_size, num_frames, channels, height, width)."
            )

        if mask_labels is not None or class_labels is not None:
            raise ValueError(
                "Training with 5D video inputs is not supported in `VideomtForUniversalSegmentation`. "
                "Flatten frames and use `EomtForUniversalSegmentation` instead."
            )

        batch_size, num_frames, num_channels, height, width = pixel_values_videos.shape
        flat_pixel_values = pixel_values_videos.reshape(batch_size * num_frames, num_channels, height, width)

        hidden_states = self.embeddings(flat_pixel_values)
        query_start_idx = self.num_hidden_layers - self.config.num_blocks

        for layer_module in self.layers[:query_start_idx]:
            hidden_states = layer_module(hidden_states)

        hidden_states = hidden_states.view(batch_size, num_frames, hidden_states.shape[1], hidden_states.shape[2])

        all_masks_queries_logits = []
        all_class_queries_logits = []
        all_last_hidden_states = []
        propagated_query = None

        for frame_idx in range(num_frames):
            frame_hidden_states = hidden_states[:, frame_idx]

            if propagated_query is None:
                query_tokens = self.query.weight[None, :, :].expand(batch_size, -1, -1).to(frame_hidden_states.device)
            else:
                query_tokens = self.query_updater(propagated_query).to(frame_hidden_states.device) + self.query.weight[
                    None, :, :
                ].to(frame_hidden_states.device)
            frame_hidden_states = torch.cat((query_tokens, frame_hidden_states), dim=1)

            for layer_module in self.layers[query_start_idx:]:
                frame_hidden_states = layer_module(frame_hidden_states)

            sequence_output = self.layernorm(frame_hidden_states)
            masks_queries_logits, class_queries_logits = self.predict(sequence_output)

            all_masks_queries_logits.append(masks_queries_logits)
            all_class_queries_logits.append(class_queries_logits)
            all_last_hidden_states.append(sequence_output)
            propagated_query = frame_hidden_states[:, : self.config.num_queries, :]

        return VideomtForUniversalSegmentationOutput(
            loss=None,  # Training not supported yet
            masks_queries_logits=torch.cat(all_masks_queries_logits, dim=0),
            class_queries_logits=torch.cat(all_class_queries_logits, dim=0),
            last_hidden_state=torch.cat(all_last_hidden_states, dim=0),
        )