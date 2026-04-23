def test_processor_text_has_no_visual(self):
        """
        Tests that multimodal models can process batch of inputs where samples can
        be with images/videos or without. See https://github.com/huggingface/transformers/issues/40263
        """
        processor = self.get_processor()
        call_signature = inspect.signature(processor.__call__)
        input_args = [param.name for param in call_signature.parameters.values() if param.annotation != param.empty]

        if not ("text" in input_args and ("images" in input_args and "videos" in input_args)):
            self.skipTest(f"{self.processor_class} doesn't support several vision modalities with text.")

        # Prepare inputs and filter by input signature. Make sure to use a high batch size, we'll set some
        # samples to text-only later
        text = self.prepare_text_inputs(batch_size=3, modalities=["image", "video"])
        image_inputs = self.prepare_image_inputs(batch_size=3)
        video_inputs = self.prepare_video_inputs(batch_size=3)
        inputs_dict = {"text": text, "images": image_inputs, "videos": video_inputs}
        inputs_dict = {k: v for k, v in inputs_dict.items() if k in input_args}

        processing_kwargs = {"return_tensors": "pt", "padding": True}
        if "videos" in inputs_dict:
            processing_kwargs["do_sample_frames"] = False

        # First call processor with all inputs and use nested input type, which is the format supported by all multimodal processors
        image_inputs_nested = [[image] if not isinstance(image, list) else image for image in image_inputs]
        video_inputs_nested = [[video] for video in video_inputs]
        inputs_dict_nested = {"text": text, "images": image_inputs_nested, "videos": video_inputs_nested}
        inputs_dict_nested = {k: v for k, v in inputs_dict_nested.items() if k in input_args}
        inputs = processor(**inputs_dict_nested, **processing_kwargs)
        self.assertTrue(self.text_input_name in inputs)

        # Now call with one of the samples with no associated vision input. Let's set the first input to be a plain text
        # with no placeholder tokens and no images/videos. The final format would be `images = [[], [image2], [image3]]`
        plain_text = "lower newer"
        image_inputs_nested[0] = []
        video_inputs_nested[0] = []
        text[0] = plain_text
        inputs_dict_no_vision = {"text": text, "images": image_inputs_nested, "videos": video_inputs_nested}
        inputs_dict_no_vision = {k: v for k, v in inputs_dict_no_vision.items() if k in input_args}
        inputs_nested = processor(**inputs_dict_no_vision, **processing_kwargs)

        # Check that text samples are same and are expanded with placeholder tokens correctly. First sample
        # has no vision input associated, so we skip it and check it has no vision
        self.assertListEqual(
            inputs[self.text_input_name][1:].tolist(), inputs_nested[self.text_input_name][1:].tolist()
        )

        # Now test if we can apply chat templates with no vision inputs in one of the samples
        # NOTE: we don't skip the test as we want the above to be checked even if process has to chat template
        if processor.chat_template is not None:
            messages = [
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is the capital of France?"},
                        ],
                    },
                ],
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is the capital of France?"},
                            {
                                "type": "image",
                                "url": url_to_local_path(
                                    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/coco_sample.png"
                                ),
                            },
                        ],
                    },
                ],
            ]

            inputs_chat_template = processor.apply_chat_template(
                messages,
                add_generation_prompt=False,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                processor_kwargs={"padding": True},
            )
            self.assertTrue(self.text_input_name in inputs_chat_template)