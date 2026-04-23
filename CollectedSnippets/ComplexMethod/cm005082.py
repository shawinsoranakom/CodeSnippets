def _get_object_pointers(
        self,
        inference_session: EdgeTamVideoInferenceSession,
        obj_idx: int,
        frame_idx: int,
        num_total_frames: int,
        device: torch.device,
        track_in_reverse_time: bool = False,
        streaming: bool = False,
    ) -> tuple[list[int], list[torch.Tensor], int]:
        """
        Get object pointers and their positional embeddings from past frames.

        Returns:
            Tuple of (temporal_offsets, pointer_tokens, max_object_pointers_to_use).
        """
        temporal_position_sign_multiplier = -1 if track_in_reverse_time else 1

        # Determine max object pointers to use
        if streaming:
            max_object_pointers_to_use = self.config.max_object_pointers_in_encoder
        else:
            max_object_pointers_to_use = min(num_total_frames, self.config.max_object_pointers_in_encoder)

        temporal_offsets: list[int] = []
        pointer_tokens: list[torch.Tensor] = []

        # Add object pointers from selected conditioning frames
        # Optionally, only include pointers from past frames during evaluation
        conditioning_outputs = inference_session.output_dict_per_obj[obj_idx]["cond_frame_outputs"]
        eligible_conditioning_outputs = conditioning_outputs
        if not self.training:
            eligible_conditioning_outputs = {
                temporal_idx: out
                for temporal_idx, out in conditioning_outputs.items()
                if (temporal_idx >= frame_idx if track_in_reverse_time else temporal_idx <= frame_idx)
            }

        for temporal_idx, out_data in eligible_conditioning_outputs.items():
            temporal_difference = (frame_idx - temporal_idx) * temporal_position_sign_multiplier
            temporal_offsets.append(temporal_difference)
            pointer_tokens.append(out_data["object_pointer"].to(device))

        # Add object pointers from non-conditioning frames (up to max_object_pointers_to_use - 1)
        for t_diff_offset in range(1, max_object_pointers_to_use):
            ref_frame_idx = frame_idx + t_diff_offset if track_in_reverse_time else frame_idx - t_diff_offset
            if ref_frame_idx < 0 or (
                not streaming and num_total_frames is not None and ref_frame_idx >= num_total_frames
            ):
                break  # Stop if frame index is out of bounds

            # check if the output is already stored without using get_output to avoid unnecessary memory transfers between CPU and GPU
            out_data = inference_session.output_dict_per_obj[obj_idx]["non_cond_frame_outputs"].get(
                ref_frame_idx, None
            )
            if out_data is not None:
                temporal_offsets.append(t_diff_offset)
                pointer_tokens.append(out_data["object_pointer"].to(device))

        return temporal_offsets, pointer_tokens, max_object_pointers_to_use