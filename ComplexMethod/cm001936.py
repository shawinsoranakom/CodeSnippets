def test_inference_video_propagate_with_text_prompt(self):
        raw_video = prepare_video()
        inference_session = self.processor.init_video_session(
            video=raw_video,
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

        # Propagate through video frames
        outputs_per_frame = {}
        model_outputs_per_frame = {}
        for model_outputs in self.video_model.propagate_in_video_iterator(
            inference_session=inference_session,
            max_frame_num_to_track=3,
        ):
            processed_outputs = self.processor.postprocess_outputs(inference_session, model_outputs)
            outputs_per_frame[model_outputs.frame_idx] = processed_outputs
            model_outputs_per_frame[model_outputs.frame_idx] = model_outputs

        # Check we processed the expected number of frames
        self.assertGreaterEqual(len(outputs_per_frame), 1)
        self.assertLessEqual(len(outputs_per_frame), 4)  # frame 0 + up to 3 more

        # Check output structure for each frame
        for processed_outputs in outputs_per_frame.values():
            self.assertIn("object_ids", processed_outputs)
            self.assertIn("scores", processed_outputs)
            self.assertIn("boxes", processed_outputs)
            self.assertIn("masks", processed_outputs)

            num_objects = len(processed_outputs["object_ids"])
            if num_objects > 0:
                self.assertEqual(processed_outputs["scores"].shape, (num_objects,))
                self.assertEqual(processed_outputs["boxes"].shape, (num_objects, 4))
                self.assertEqual(
                    processed_outputs["masks"].shape, (num_objects, raw_video.shape[-3], raw_video.shape[-2])
                )
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
                    torch.tensor([0.968647837638855, 0.9736108779907227], dtype=torch.float32),
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
                                [-2.952317476272583, -5.94632625579834, -7.991223335266113],
                                [-6.916913986206055, -10.058566093444824, -11.114638328552246],
                                [-8.195585250854492, -9.787644386291504, -10.39273452758789],
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
                    torch.tensor([0.968647837638855, 0.9736108779907227], dtype=torch.float32),
                    atol=1e-4,
                    rtol=1e-4,
                )
                torch.testing.assert_close(
                    boxes[0],
                    torch.tensor([157.0, 116.0, 295.0, 382.0], dtype=torch.float32),
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
                                [-23.023313522338867, -27.02887535095215, -22.29985237121582],
                                [-24.373233795166016, -31.428438186645508, -24.268810272216797],
                                [-24.550016403198242, -32.607383728027344, -26.500947952270508],
                            ]
                        ],
                        dtype=torch.float32,
                    ),
                    atol=5e-3,  # Higher tolerance for raw logits
                    rtol=5e-3,
                )