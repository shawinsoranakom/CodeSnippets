def add_inputs_to_inference_session(
        self,
        inference_session: Sam3TrackerVideoInferenceSession,
        frame_idx: int,
        obj_ids: list[int] | int,
        input_points: list[list[list[list[float]]]] | torch.Tensor | None = None,
        input_labels: list[list[list[int]]] | torch.Tensor | None = None,
        input_boxes: list[list[list[float]]] | torch.Tensor | None = None,
        input_masks: np.ndarray | torch.Tensor | list[np.ndarray] | list[torch.Tensor] | None = None,
        original_size: tuple[int, int] | None = None,
        clear_old_inputs: bool = True,
    ) -> Sam3TrackerVideoInferenceSession:
        """
        Process new points, boxes, or masks for a video frame and add them to the inference session.

        Args:
            inference_session (`Sam3TrackerVideoInferenceSession`):
                The inference session for the video.
            frame_idx (`int`):
                The index of the frame to process.
            obj_ids (`list[int]` or `int`):
                The object ID(s) to associate with the points or box.
                These can be any integers and can be reused later on to specify an object.
            input_points (`list[list[list[list[float]]]]`, `torch.Tensor`, *optional*):
                The points to add to the frame.
            input_labels (`list[list[list[int]]]`, `torch.Tensor`, *optional*):
                The labels for the points.
            input_boxes (`list[list[list[float]]]`, `torch.Tensor`, *optional*):
                The bounding boxes to add to the frame.
            input_masks (`np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, or `list[torch.Tensor]`, *optional*):
                The mask(s) to add to the frame.
            original_size (`tuple[int, int]`, *optional*):
                The original size of the video. Provide when streaming.
            clear_old_inputs (`bool`, *optional*, defaults to `True`):
                Whether to clear old inputs for the object.
        """

        if isinstance(obj_ids, int):
            obj_ids = [obj_ids]

        # Validate inputs
        if (input_points is not None) != (input_labels is not None):
            raise ValueError("points and labels must be provided together")
        if input_points is None and input_boxes is None and input_masks is None:
            raise ValueError("at least one of points, boxes, or masks must be provided as input")
        if input_masks is not None and (input_points is not None or input_boxes is not None):
            raise ValueError("masks cannot be provided together with points or boxes")

        if input_masks is not None:
            return self.process_new_mask_for_video_frame(inference_session, frame_idx, obj_ids, input_masks)
        else:
            return self.process_new_points_or_boxes_for_video_frame(
                inference_session,
                frame_idx,
                obj_ids,
                input_points,
                input_labels,
                input_boxes,
                original_size,
                clear_old_inputs,
            )