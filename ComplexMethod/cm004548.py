def _match_image_pair(
        self,
        keypoints: torch.Tensor,
        descriptors: torch.Tensor,
        scores: torch.Tensor,
        height: int,
        width: int,
        mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, tuple, tuple]:
        """
        Perform keypoint matching between two images.

        Args:
            keypoints (`torch.Tensor` of shape `(batch_size, 2, num_keypoints, 2)`):
                Keypoints detected in the pair of image.
            descriptors (`torch.Tensor` of shape `(batch_size, 2, descriptor_dim, num_keypoints)`):
                Descriptors of the keypoints detected in the image pair.
            scores (`torch.Tensor` of shape `(batch_size, 2, num_keypoints)`):
                Confidence scores of the keypoints detected in the image pair.
            height (`int`): Image height.
            width (`int`): Image width.
            mask (`torch.Tensor` of shape `(batch_size, 2, num_keypoints)`, *optional*):
                Mask indicating which values in the keypoints, matches and matching_scores tensors are keypoint matching
                information.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors. Default to `config.output_attentions`.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. Default to `config.output_hidden_states`.

        Returns:
            matches (`torch.Tensor` of shape `(batch_size, 2, num_keypoints)`):
                For each image pair, for each keypoint in image0, the index of the keypoint in image1 that was matched
                with. And for each keypoint in image1, the index of the keypoint in image0 that was matched with.
            matching_scores (`torch.Tensor` of shape `(batch_size, 2, num_keypoints)`):
                Scores of predicted matches for each image pair
            all_hidden_states (`tuple(torch.FloatTensor)`, *optional*):
                Tuple of `torch.FloatTensor` (one for the output of each stage) of shape `(1, 2, num_keypoints,
                num_channels)`.
            all_attentions (`tuple(torch.FloatTensor)`, *optional*):
                Tuple of `torch.FloatTensor` (one for each layer) of shape `(1, 2, num_heads, num_keypoints,
                num_keypoints)`.
        """
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        if keypoints.shape[2] == 0:  # no keypoints
            shape = keypoints.shape[:-1]
            return (
                keypoints.new_full(shape, -1, dtype=torch.int),
                keypoints.new_zeros(shape),
                all_hidden_states,
                all_attentions,
            )

        batch_size, _, num_keypoints, _ = keypoints.shape
        # (batch_size, 2, num_keypoints, 2) -> (batch_size * 2, num_keypoints, 2)
        keypoints = keypoints.reshape(batch_size * 2, num_keypoints, 2)
        descriptors = descriptors.reshape(batch_size * 2, num_keypoints, self.config.hidden_size)
        scores = scores.reshape(batch_size * 2, num_keypoints)
        mask = mask.reshape(batch_size * 2, num_keypoints) if mask is not None else None

        # Keypoint normalization
        keypoints = normalize_keypoints(keypoints, height, width)

        encoded_keypoints = self.keypoint_encoder(keypoints, scores, output_hidden_states=output_hidden_states)

        last_hidden_state = encoded_keypoints[0]

        # Keypoint MLP encoder.
        descriptors = descriptors + last_hidden_state

        if mask is not None:
            input_shape = descriptors.size()
            extended_attention_mask = self.get_extended_attention_mask(mask, input_shape)
        else:
            extended_attention_mask = torch.ones((batch_size, num_keypoints), device=keypoints.device)

        # Multi-layer Transformer network.
        gnn_outputs = self.gnn(
            descriptors,
            mask=extended_attention_mask,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
        )
        descriptors = gnn_outputs[0]

        # Final MLP projection.
        projected_descriptors = self.final_projection(descriptors)

        # (batch_size * 2, num_keypoints, descriptor_dim) -> (batch_size, 2, num_keypoints, descriptor_dim)
        final_descriptors = projected_descriptors.reshape(batch_size, 2, num_keypoints, self.config.hidden_size)
        final_descriptors0 = final_descriptors[:, 0]
        final_descriptors1 = final_descriptors[:, 1]

        # Compute matching descriptor distance.
        scores = final_descriptors0 @ final_descriptors1.transpose(1, 2)
        scores = scores / self.config.hidden_size**0.5

        if mask is not None:
            mask = mask.reshape(batch_size, 2, num_keypoints)
            mask0 = mask[:, 0].unsqueeze(2)
            mask1 = mask[:, 1].unsqueeze(1)
            mask = torch.logical_and(mask0, mask1)
            scores = scores.masked_fill(mask == 0, torch.finfo(scores.dtype).min)

        # Run the optimal transport.
        scores = log_optimal_transport(scores, self.bin_score, iterations=self.config.sinkhorn_iterations)

        # Get the matches with score above "match_threshold".
        max0 = scores[:, :-1, :-1].max(2)
        max1 = scores[:, :-1, :-1].max(1)
        indices0 = max0.indices
        indices1 = max1.indices
        mutual0 = arange_like(indices0, 1)[None] == indices1.gather(1, indices0)
        mutual1 = arange_like(indices1, 1)[None] == indices0.gather(1, indices1)
        zero = scores.new_tensor(0)
        matching_scores0 = torch.where(mutual0, max0.values.exp(), zero)
        matching_scores0 = torch.where(matching_scores0 > self.config.matching_threshold, matching_scores0, zero)
        matching_scores1 = torch.where(mutual1, matching_scores0.gather(1, indices1), zero)
        valid0 = mutual0 & (matching_scores0 > zero)
        valid1 = mutual1 & valid0.gather(1, indices1)
        matches0 = torch.where(valid0, indices0, indices0.new_tensor(-1))
        matches1 = torch.where(valid1, indices1, indices1.new_tensor(-1))

        matches = torch.cat([matches0, matches1], dim=1).reshape(batch_size, 2, -1)
        matching_scores = torch.cat([matching_scores0, matching_scores1], dim=1).reshape(batch_size, 2, -1)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + encoded_keypoints[1]
            all_hidden_states = all_hidden_states + gnn_outputs[1]
            all_hidden_states = all_hidden_states + (projected_descriptors,)
            all_hidden_states = tuple(
                x.reshape(batch_size, 2, num_keypoints, -1).transpose(-1, -2) for x in all_hidden_states
            )
        if output_attentions:
            all_attentions = all_attentions + gnn_outputs[2]
            all_attentions = tuple(x.reshape(batch_size, 2, -1, num_keypoints, num_keypoints) for x in all_attentions)

        return (
            matches,
            matching_scores,
            all_hidden_states,
            all_attentions,
        )