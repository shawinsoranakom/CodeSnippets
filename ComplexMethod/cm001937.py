def test_inference_video_streaming_with_text_prompt(self):
        raw_video = prepare_video()

        # Initialize session for streaming (no video provided)
        inference_session = self.processor.init_video_session(
            inference_device=torch_device,
            processing_device="cpu",
            video_storage_device="cpu",
        )

        # Add text prompt
        text = "person"
        inference_session = self.processor.add_text_prompt(
            inference_session=inference_session,
            text=text,
        )

        # Process frames one by one (streaming mode)
        outputs_per_frame = {}
        model_outputs_per_frame = {}
        max_frame_num_to_track = 3
        for frame_idx, frame in enumerate(raw_video):
            if frame_idx >= max_frame_num_to_track:
                break

            # Process frame using processor
            inputs = self.processor(images=frame, device=torch_device, return_tensors="pt")

            # Process frame using streaming inference
            model_outputs = self.video_model(
                inference_session=inference_session,
                frame=inputs.pixel_values[0],  # Provide processed frame - this enables streaming mode
                reverse=False,
            )

            # Post-process outputs with original_sizes for proper resolution handling
            processed_outputs = self.processor.postprocess_outputs(
                inference_session,
                model_outputs,
                original_sizes=inputs.original_sizes,  # Required for streaming inference
            )
            outputs_per_frame[frame_idx] = processed_outputs
            model_outputs_per_frame[frame_idx] = model_outputs

        # Check we processed the expected number of frames
        self.assertEqual(len(outputs_per_frame), max_frame_num_to_track)

        # Check output structure for each frame
        for frame_idx, processed_outputs in outputs_per_frame.items():
            self.assertIn("object_ids", processed_outputs)
            self.assertIn("scores", processed_outputs)
            self.assertIn("boxes", processed_outputs)
            self.assertIn("masks", processed_outputs)

            num_objects = len(processed_outputs["object_ids"])
            if num_objects > 0:
                self.assertEqual(processed_outputs["scores"].shape, (num_objects,))
                self.assertEqual(processed_outputs["boxes"].shape, (num_objects, 4))
                # For streaming, masks should be at original frame resolution
                H_orig, W_orig = raw_video[frame_idx].shape[0], raw_video[frame_idx].shape[1]
                self.assertEqual(processed_outputs["masks"].shape, (num_objects, H_orig, W_orig))
                # Check boxes are in XYXY format (absolute coordinates)
                boxes = processed_outputs["boxes"]
                self.assertTrue(torch.all(boxes[:, 2] >= boxes[:, 0]))  # x2 >= x1
                self.assertTrue(torch.all(boxes[:, 3] >= boxes[:, 1]))  # y2 >= y1

        # Check numeric values for first frame
        if len(outputs_per_frame) > 0:
            first_frame_idx = min(outputs_per_frame.keys())
            first_outputs = outputs_per_frame[first_frame_idx]
            num_objects = len(first_outputs["object_ids"])
            if num_objects > 0:
                # Move outputs to CPU for comparison (postprocess_outputs may return CPU tensors)
                object_ids = (
                    first_outputs["object_ids"].cpu()
                    if isinstance(first_outputs["object_ids"], torch.Tensor)
                    else torch.tensor(first_outputs["object_ids"])
                )
                scores = (
                    first_outputs["scores"].cpu()
                    if isinstance(first_outputs["scores"], torch.Tensor)
                    else torch.tensor(first_outputs["scores"])
                )
                boxes = (
                    first_outputs["boxes"].cpu()
                    if isinstance(first_outputs["boxes"], torch.Tensor)
                    else torch.tensor(first_outputs["boxes"])
                )
                masks = (
                    first_outputs["masks"].cpu()
                    if isinstance(first_outputs["masks"], torch.Tensor)
                    else torch.tensor(first_outputs["masks"])
                )

                torch.testing.assert_close(
                    object_ids,
                    torch.tensor([0, 1], dtype=torch.int64),
                )
                torch.testing.assert_close(
                    scores,
                    torch.tensor([0.9683944582939148, 0.9740181565284729], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )
                torch.testing.assert_close(
                    boxes[0],
                    torch.tensor([146.0, 135.0, 291.0, 404.0], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )
                torch.testing.assert_close(
                    masks[0, :3, :3].float(),
                    torch.tensor([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )

        # Check raw model_outputs mask values for first frame
        if len(model_outputs_per_frame) > 0:
            first_frame_idx = min(model_outputs_per_frame.keys())
            first_model_outputs = model_outputs_per_frame[first_frame_idx]
            num_objects = len(first_model_outputs.object_ids)
            if num_objects > 0:
                # Check raw mask from model_outputs (low-resolution, before post-processing)
                first_obj_id = first_model_outputs.object_ids[0]
                raw_mask = first_model_outputs.obj_id_to_mask[first_obj_id].cpu()
                torch.testing.assert_close(
                    raw_mask[:1, :3, :3].float(),
                    torch.tensor(
                        [
                            [
                                [-2.987567901611328, -5.944897651672363, -7.973854064941406],
                                [-7.017378330230713, -10.088018417358398, -11.089308738708496],
                                [-8.274458885192871, -9.851463317871094, -10.428947448730469],
                            ]
                        ],
                        dtype=torch.float32,
                    ),
                    atol=5e-3,  # Higher tolerance for raw logits
                    rtol=5e-3,
                )

        # Check numeric values for last frame (to verify propagation consistency)
        if len(outputs_per_frame) > 1:
            last_frame_idx = max(outputs_per_frame.keys())
            last_outputs = outputs_per_frame[last_frame_idx]
            num_objects = len(last_outputs["object_ids"])
            if num_objects > 0:
                # Move outputs to CPU for comparison
                object_ids = (
                    last_outputs["object_ids"].cpu()
                    if isinstance(last_outputs["object_ids"], torch.Tensor)
                    else torch.tensor(last_outputs["object_ids"])
                )
                scores = (
                    last_outputs["scores"].cpu()
                    if isinstance(last_outputs["scores"], torch.Tensor)
                    else torch.tensor(last_outputs["scores"])
                )
                boxes = (
                    last_outputs["boxes"].cpu()
                    if isinstance(last_outputs["boxes"], torch.Tensor)
                    else torch.tensor(last_outputs["boxes"])
                )
                masks = (
                    last_outputs["masks"].cpu()
                    if isinstance(last_outputs["masks"], torch.Tensor)
                    else torch.tensor(last_outputs["masks"])
                )

                torch.testing.assert_close(
                    object_ids,
                    torch.tensor([0, 1], dtype=torch.int64),
                )
                torch.testing.assert_close(
                    scores,
                    torch.tensor([0.9683944582939148, 0.9740181565284729], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )
                torch.testing.assert_close(
                    boxes[0],
                    torch.tensor([154.0, 117.0, 294.0, 395.0], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )
                torch.testing.assert_close(
                    masks[0, :3, :3].float(),
                    torch.tensor([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )

        # Check raw model_outputs mask values for last frame
        if len(model_outputs_per_frame) > 1:
            last_frame_idx = max(model_outputs_per_frame.keys())
            last_model_outputs = model_outputs_per_frame[last_frame_idx]
            num_objects = len(last_model_outputs.object_ids)
            if num_objects > 0:
                # Check raw mask from model_outputs (low-resolution, before post-processing)
                first_obj_id = last_model_outputs.object_ids[0]
                raw_mask = last_model_outputs.obj_id_to_mask[first_obj_id].cpu()
                torch.testing.assert_close(
                    raw_mask[:1, :3, :3].float(),
                    torch.tensor(
                        [
                            [
                                [-23.935535430908203, -27.967025756835938, -23.519914627075195],
                                [-25.742399215698242, -32.65046310424805, -24.71213150024414],
                                [-25.263212203979492, -33.807132720947266, -27.463823318481445],
                            ]
                        ],
                        dtype=torch.float32,
                    ),
                    atol=5e-3,  # Higher tolerance for raw logits
                    rtol=5e-3,
                )