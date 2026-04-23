def test_apply_chat_template_video_frame_sampling(self):
        processor = self.get_processor()
        if processor.chat_template is None:
            self.skipTest("Processor has no chat template")

        signature = inspect.signature(processor.__call__)
        if "videos" not in {*signature.parameters.keys()} or (
            signature.parameters.get("videos") is not None
            and signature.parameters["videos"].annotation == inspect._empty
        ):
            self.skipTest("Processor doesn't accept videos at input")

        messages = [
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is shown in this video?"},
                    ],
                },
            ]
        ]

        formatted_prompt = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        self.assertEqual(len(formatted_prompt), 1)

        formatted_prompt_tokenized = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
        expected_output = processor.tokenizer(formatted_prompt, return_tensors=None).input_ids
        self.assertListEqual(expected_output, formatted_prompt_tokenized)

        out_dict = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_dict=True)
        self.assertListEqual(list(out_dict.keys()), ["input_ids", "attention_mask"])

        # Add video URL for return dict and load with `num_frames` arg
        messages[0][0]["content"].append(
            {
                "type": "video",
                "url": url_to_local_path(
                    "https://huggingface.co/datasets/raushan-testing-hf/videos-test/resolve/main/tiny_video.mp4"
                ),
            }
        )
        num_frames = 3
        out_dict_with_video = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            num_frames=num_frames,
        )
        self.assertTrue(self.videos_input_name in out_dict_with_video)
        # Qwen pixel values are flattened, verify length matches video_grid_thw
        expected_video_tokens = sum(thw[0] * thw[1] * thw[2] for thw in out_dict_with_video["video_grid_thw"])
        self.assertEqual(len(out_dict_with_video[self.videos_input_name]), expected_video_tokens)

        # Load with `fps` arg
        fps = 1
        out_dict_with_video = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            fps=fps,
        )
        self.assertTrue(self.videos_input_name in out_dict_with_video)
        expected_video_tokens = sum(thw[0] * thw[1] * thw[2] for thw in out_dict_with_video["video_grid_thw"])
        self.assertEqual(len(out_dict_with_video[self.videos_input_name]), expected_video_tokens)

        # Load with `fps` and `num_frames` args, should raise an error
        with self.assertRaises(ValueError):
            out_dict_with_video = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                fps=fps,
                num_frames=num_frames,
            )

        # Load without any arg should load the whole video
        out_dict_with_video = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
        )
        self.assertTrue(self.videos_input_name in out_dict_with_video)
        expected_video_tokens = sum(thw[0] * thw[1] * thw[2] for thw in out_dict_with_video["video_grid_thw"])
        self.assertEqual(len(out_dict_with_video[self.videos_input_name]), expected_video_tokens)

        # Load video as a list of frames (i.e. images). NOTE: each frame should have same size
        # because we assume they come from one video
        messages[0][0]["content"][-1] = {
            "type": "video",
            "url": [
                url_to_local_path(
                    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/tasks/australia.jpg"
                ),
                url_to_local_path(
                    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/tasks/australia.jpg"
                ),
            ],
        }
        out_dict_with_video = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
        )
        self.assertTrue(self.videos_input_name in out_dict_with_video)
        expected_video_tokens = sum(thw[0] * thw[1] * thw[2] for thw in out_dict_with_video["video_grid_thw"])
        self.assertEqual(len(out_dict_with_video[self.videos_input_name]), expected_video_tokens)

        # When the inputs are frame URLs/paths we expect that those are already
        # sampled and will raise an error is asked to sample again.
        with self.assertRaisesRegex(
            ValueError, "Sampling frames from a list of images is not supported! Set `do_sample_frames=False`"
        ):
            out_dict_with_video = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                do_sample_frames=True,
            )