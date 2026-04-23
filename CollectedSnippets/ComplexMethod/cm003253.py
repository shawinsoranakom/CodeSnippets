def _match_image_pair(
        self,
        keypoints: torch.Tensor,
        descriptors: torch.Tensor,
        height: int,
        width: int,
        mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, tuple, tuple]:
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        if keypoints.shape[2] == 0:  # no keypoints
            shape = keypoints.shape[:-1]
            return (
                keypoints.new_full(shape, -1, dtype=torch.int),
                keypoints.new_zeros(shape),
                keypoints.new_zeros(shape),
                all_hidden_states,
                all_attentions,
            )

        device = keypoints.device
        batch_size, _, initial_num_keypoints, _ = keypoints.shape
        num_points_per_pair = torch.sum(mask.reshape(batch_size, -1), dim=1)
        # (batch_size, 2, num_keypoints, 2) -> (batch_size * 2, num_keypoints, 2)
        keypoints = keypoints.reshape(batch_size * 2, initial_num_keypoints, 2)
        mask = mask.reshape(batch_size * 2, initial_num_keypoints) if mask is not None else None
        descriptors = descriptors.reshape(batch_size * 2, initial_num_keypoints, self.keypoint_detector_descriptor_dim)
        image_indices = torch.arange(batch_size * 2, device=device)
        # Keypoint normalization
        keypoints = normalize_keypoints(keypoints, height, width)

        descriptors, keypoint_encoding_output = self._keypoint_processing(
            descriptors, keypoints, output_hidden_states=output_hidden_states
        )

        keypoints = keypoint_encoding_output[0]

        # Early stop consists of stopping the forward pass through the transformer layers when the confidence of the
        # keypoints is above a certain threshold.
        do_early_stop = self.depth_confidence > 0
        # Keypoint pruning consists of removing keypoints from the input of the transformer layers when the confidence of
        # the keypoints is below a certain threshold.
        do_keypoint_pruning = self.width_confidence > 0

        early_stops_indices = []
        matches = []
        matching_scores = []
        final_pruned_keypoints_indices = []
        final_pruned_keypoints_iterations = []

        pruned_keypoints_indices = torch.arange(0, initial_num_keypoints, device=device).expand(batch_size * 2, -1)
        pruned_keypoints_iterations = torch.ones_like(pruned_keypoints_indices)

        for layer_index in range(self.num_layers):
            input_shape = descriptors.size()
            if mask is not None:
                extended_attention_mask = self.get_extended_attention_mask(mask, input_shape)
            else:
                extended_attention_mask = torch.ones((batch_size, input_shape[-2]), device=keypoints.device)
            layer_output = self.transformer_layers[layer_index](
                descriptors,
                keypoints,
                attention_mask=extended_attention_mask,
                output_hidden_states=output_hidden_states,
                output_attentions=output_attentions,
            )
            descriptors, hidden_states, attention = layer_output
            if output_hidden_states:
                all_hidden_states = all_hidden_states + hidden_states
            if output_attentions:
                all_attentions = all_attentions + attention

            if do_early_stop:
                if layer_index < self.num_layers - 1:
                    # Get the confidence of the keypoints for the current layer
                    keypoint_confidences = self.token_confidence[layer_index](descriptors)

                    # Determine which pairs of images should be early stopped based on the confidence of the keypoints for
                    # the current layer.
                    early_stopped_pairs = self._get_early_stopped_image_pairs(
                        keypoint_confidences, layer_index, mask, num_points=num_points_per_pair
                    )
                else:
                    # Early stopping always occurs at the last layer
                    early_stopped_pairs = torch.ones(batch_size, dtype=torch.bool)

                if torch.any(early_stopped_pairs):
                    # If a pair of images is considered early stopped, we compute the matches for the remaining
                    # keypoints and stop the forward pass through the transformer layers for this pair of images.
                    early_stops = early_stopped_pairs.repeat_interleave(2)
                    early_stopped_image_indices = image_indices[early_stops]
                    early_stopped_matches, early_stopped_matching_scores = self._get_keypoint_matching(
                        descriptors, mask, layer_index, early_stops=early_stops
                    )
                    early_stops_indices.extend(list(early_stopped_image_indices))
                    matches.extend(list(early_stopped_matches))
                    matching_scores.extend(list(early_stopped_matching_scores))
                    if do_keypoint_pruning:
                        final_pruned_keypoints_indices.extend(list(pruned_keypoints_indices[early_stops]))
                        final_pruned_keypoints_iterations.extend(list(pruned_keypoints_iterations[early_stops]))

                    # Remove image pairs that have been early stopped from the forward pass
                    num_points_per_pair = num_points_per_pair[~early_stopped_pairs]
                    descriptors, keypoints_0, keypoint_1, mask, image_indices = tuple(
                        tensor[~early_stops]
                        for tensor in [descriptors, keypoints[0], keypoints[1], mask, image_indices]
                    )
                    keypoints = (keypoints_0, keypoint_1)
                    if do_keypoint_pruning:
                        pruned_keypoints_indices, pruned_keypoints_iterations, keypoint_confidences = tuple(
                            tensor[~early_stops]
                            for tensor in [
                                pruned_keypoints_indices,
                                pruned_keypoints_iterations,
                                keypoint_confidences,
                            ]
                        )
                # If all pairs of images are early stopped, we stop the forward pass through the transformer
                # layers for all pairs of images.
                if torch.all(early_stopped_pairs):
                    break

            if do_keypoint_pruning:
                # Prune keypoints from the input of the transformer layers for the next iterations if the confidence of
                # the keypoints is below a certain threshold.
                descriptors, keypoints, pruned_keypoints_indices, mask, pruned_keypoints_iterations = (
                    self._do_layer_keypoint_pruning(
                        descriptors,
                        keypoints,
                        mask,
                        pruned_keypoints_indices,
                        pruned_keypoints_iterations,
                        keypoint_confidences,
                        layer_index,
                    )
                )

        if do_early_stop and do_keypoint_pruning:
            # Concatenate early stopped outputs together and perform final keypoint pruning
            final_pruned_keypoints_indices, final_pruned_keypoints_iterations, matches, matching_scores = (
                self._concat_early_stopped_outputs(
                    early_stops_indices,
                    final_pruned_keypoints_indices,
                    final_pruned_keypoints_iterations,
                    matches,
                    matching_scores,
                )
            )
            matches, matching_scores = self._do_final_keypoint_pruning(
                final_pruned_keypoints_indices,
                matches,
                matching_scores,
                initial_num_keypoints,
            )
        else:
            matches, matching_scores = self._get_keypoint_matching(descriptors, mask, self.num_layers - 1)
            final_pruned_keypoints_iterations = torch.ones_like(matching_scores) * self.num_layers

        final_pruned_keypoints_iterations = final_pruned_keypoints_iterations.reshape(
            batch_size, 2, initial_num_keypoints
        )

        return (
            matches,
            matching_scores,
            final_pruned_keypoints_iterations,
            all_hidden_states,
            all_attentions,
        )