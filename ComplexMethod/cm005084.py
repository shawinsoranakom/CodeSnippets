def propagate_in_video_iterator(
        self,
        inference_session: EdgeTamVideoInferenceSession,
        start_frame_idx: int | None = None,
        max_frame_num_to_track: int | None = None,
        reverse: bool = False,
        show_progress_bar: bool = False,
    ) -> Iterator[EdgeTamVideoSegmentationOutput]:
        r"""
        inference_session (`EdgeTamVideoInferenceSession`):
            The video inference session object.
        start_frame_idx (`int`, *optional*):
            The starting frame index for propagation.
            Need to be provided if `forward` hasn't been called on new inputs yet.
            If not provided, the starting frame index will be the earliest frame with input points.
        max_frame_num_to_track (`int`, *optional*):
            The maximum number of frames to track.
        reverse (`bool`, *optional*, defaults to `False`):
            Whether to propagate in reverse.
        show_progress_bar (`bool`, *optional*, defaults to `False`):
            Whether to show a progress bar during propagation.
        """
        num_frames = inference_session.num_frames

        # set start index, end index, and processing order
        if start_frame_idx is None:
            # default: start from the earliest frame with input points
            frames_with_inputs = [
                frame_idx
                for obj_output_dict in inference_session.output_dict_per_obj.values()
                for frame_idx in obj_output_dict["cond_frame_outputs"]
            ]
            if not frames_with_inputs:
                raise ValueError(
                    "Cannot determine the starting frame index; please specify it manually, or run inference on a frame with inputs first."
                )
            start_frame_idx = min(frames_with_inputs)
        if max_frame_num_to_track is None:
            # default: track all the frames in the video
            max_frame_num_to_track = num_frames
        if reverse:
            end_frame_idx = max(start_frame_idx - max_frame_num_to_track, 0)
            if start_frame_idx > 0:
                processing_order = range(start_frame_idx, end_frame_idx - 1, -1)
            else:
                processing_order = []  # skip reverse tracking if starting from frame 0
        else:
            end_frame_idx = min(start_frame_idx + max_frame_num_to_track, num_frames - 1)
            processing_order = range(start_frame_idx, end_frame_idx + 1)

        for frame_idx in tqdm(processing_order, desc="propagate in video", disable=not show_progress_bar):
            edgetam_video_output = self(inference_session, frame_idx=frame_idx, reverse=reverse)
            yield edgetam_video_output