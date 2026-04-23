def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)
        videos = mm_data.pop("videos", [])
        images = mm_data.pop("images", [])
        assert isinstance(videos, list)
        assert isinstance(images, list)

        hf_processor = self.info.get_hf_processor(**mm_kwargs)
        tokenizer = hf_processor.tokenizer
        video_token_id = tokenizer.encode(
            hf_processor.video_token, add_special_tokens=False
        )
        assert len(video_token_id) == 1
        video_token_id = video_token_id[0]

        prompt = re.sub(hf_processor.image_token, "<image_placeholder>", prompt)
        prompt = re.sub(hf_processor.video_token, "<video_placeholder>", prompt)

        image_outputs = {}
        if images:
            image_pixel_values = []
            for image in images:
                processed_outputs = super()._call_hf_processor(
                    prompt=hf_processor.image_token,
                    mm_data={"images": image},
                    mm_kwargs=mm_kwargs,
                    tok_kwargs=tok_kwargs,
                )
                image_pixel_values.append(processed_outputs.pop("pixel_values"))

                input_ids = processed_outputs.pop("input_ids")
                image_placeholder = tokenizer.batch_decode(input_ids)[0]
                prompt = prompt.replace("<image_placeholder>", image_placeholder, 1)

            num_patches = [len(item) for item in image_pixel_values]
            image_outputs = {
                "pixel_values": torch.concat(image_pixel_values),
                "image_num_patches": torch.tensor(num_patches),
                "image_token_id": torch.tensor(hf_processor.image_token_id),
            }

        video_outputs = {}
        if videos:
            video_pixel_values = []
            for video in videos:
                processed_outputs = super()._call_hf_processor(
                    prompt=hf_processor.video_token,
                    mm_data={"videos": video},
                    mm_kwargs=mm_kwargs,
                    tok_kwargs=tok_kwargs,
                )
                video_pixel_values.append(processed_outputs.pop("pixel_values"))

                input_ids = processed_outputs.pop("input_ids")
                input_ids[input_ids == hf_processor.image_token_id] = video_token_id

                video_placeholder = tokenizer.batch_decode(input_ids)[0]
                prompt = prompt.replace("<video_placeholder>", video_placeholder, 1)

            num_frames = [len(item) for item in video_pixel_values]
            video_outputs = {
                "pixel_values_videos": torch.concat(video_pixel_values),
                "video_num_patches": torch.tensor(num_frames),
                "video_token_id": torch.tensor(video_token_id),
            }

        prompt = re.sub("<image_placeholder>", hf_processor.image_token, prompt)
        prompt = re.sub("<video_placeholder>", hf_processor.video_token, prompt)
        text_outputs = tokenizer(prompt, **tok_kwargs, return_tensors="pt")

        return BatchFeature({**text_outputs, **image_outputs, **video_outputs})