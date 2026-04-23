def process_new_points_or_boxes_for_video_frame(
        self,
        inference_session: Sam2VideoInferenceSession,
        frame_idx: int,
        obj_ids: list[int],
        input_points: list[list[list[list[float]]]] | torch.Tensor | None = None,
        input_labels: list[list[list[int]]] | torch.Tensor | None = None,
        input_boxes: list[list[list[float]]] | torch.Tensor | None = None,
        original_size: tuple[int, int] | None = None,
        clear_old_inputs: bool = True,
    ) -> Sam2VideoInferenceSession:
        """
        Process new points or boxes for a video frame and add them to the inference session.

        Args:
            inference_session (`Sam2VideoInferenceSession`):
                The inference session for the video.
            frame_idx (`int`):
                The index of the frame to process.
            obj_ids (`list[int]`):
                The object ID(s) to associate with the points or box.
                These can be any integers and can be reused later on to specify an object.
            input_points (`list[list[list[list[float]]]]`, `torch.Tensor`, *optional*):
                The points to add to the frame.
            input_labels (`list[list[list[int]]]`, `torch.Tensor`, *optional*):
                The labels for the points.
            input_boxes (`list[list[list[float]]]`, `torch.Tensor`, *optional*):
                The bounding boxes to add to the frame.
            original_size (`tuple[int, int]`, *optional*):
                The original size of the video. Provide when streaming.
            clear_old_inputs (`bool`, *optional*, defaults to `True`):
                Whether to clear old inputs for the object.
        """
        if original_size is not None:
            inference_session.video_height = original_size[0]
            inference_session.video_width = original_size[1]
        elif inference_session.video_height is None or inference_session.video_width is None:
            raise ValueError("original_size must be provided when adding points or boxes on a first streamed frame")

        original_sizes = [[inference_session.video_height, inference_session.video_width]]

        encoded_inputs = self(
            input_points=input_points,
            input_labels=input_labels,
            input_boxes=input_boxes,
            original_sizes=original_sizes,
            return_tensors="pt",
        )
        input_points = encoded_inputs.get("input_points", None)
        input_labels = encoded_inputs.get("input_labels", None)
        input_boxes = encoded_inputs.get("input_boxes", None)

        if input_points is not None:
            if input_points.shape[1] != len(obj_ids):
                raise ValueError(
                    f"Number of object ids ({len(obj_ids)}) does not match number of points ({input_points.shape[1]})"
                )
        else:
            input_points = torch.zeros(1, len(obj_ids), 0, 2, dtype=torch.float32)
        if input_labels is not None:
            if input_labels.shape[1] != len(obj_ids):
                raise ValueError(
                    f"Number of object ids ({len(obj_ids)}) does not match number of labels ({input_labels.shape[1]})"
                )
        else:
            input_labels = torch.zeros(1, len(obj_ids), 0, dtype=torch.int32)
        if input_boxes is not None:
            if input_boxes.shape[1] != len(obj_ids):
                raise ValueError(
                    f"Number of object ids ({len(obj_ids)}) does not match number of boxes ({input_boxes.shape[1]})"
                )

        if input_boxes is not None:
            if not clear_old_inputs:
                raise ValueError(
                    "cannot add box without clearing old points, since "
                    "box prompt must be provided before any point prompt "
                    "(please use clear_old_points=True instead)"
                )
            box_coords = input_boxes.reshape(1, -1, 2, 2)
            box_labels = torch.tensor([2, 3], dtype=torch.int32).repeat(1, box_coords.shape[1], 1)
            input_points = torch.cat([box_coords, input_points], dim=2)
            input_labels = torch.cat([box_labels, input_labels], dim=2)

        for obj_id, idx in zip(obj_ids, range(len(obj_ids))):
            obj_idx = inference_session.obj_id_to_idx(obj_id)
            input_points_for_obj = input_points[:, idx, :, :].unsqueeze(1)
            input_labels_for_obj = input_labels[:, idx, :].unsqueeze(1)
            # Handle existing points
            if not clear_old_inputs:
                existing_points = inference_session.point_inputs_per_obj[obj_idx].get(frame_idx, None)
                if existing_points is not None:
                    # Concatenate with existing points
                    input_points_for_obj = torch.cat(
                        [existing_points["point_coords"].to(input_points_for_obj.device), input_points_for_obj], dim=2
                    )
                    input_labels_for_obj = torch.cat(
                        [existing_points["point_labels"].to(input_labels_for_obj.device), input_labels_for_obj], dim=2
                    )
            point_inputs = {
                "point_coords": input_points_for_obj,
                "point_labels": input_labels_for_obj,
            }

            inference_session.add_point_inputs(obj_idx, frame_idx, point_inputs)
            inference_session.remove_mask_inputs(obj_idx, frame_idx)  # Clear any mask inputs

        inference_session.obj_with_new_inputs = obj_ids