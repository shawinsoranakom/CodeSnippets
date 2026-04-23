def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)

        hf_config = self.info.get_hf_config()
        hf_processor = self.info.get_hf_processor(**mm_kwargs)

        def patched_call(text=None, images=None, videos=None, **kwargs) -> BatchFeature:
            res = hf_processor(text=text, images=images, videos=videos, **kwargs)

            # Molmo2Processor.insert_bos results in float outputs
            # if the input text is empty
            if not text:
                res["input_ids"] = res["input_ids"].long()

            return res

        tokenizer = hf_processor.tokenizer
        image_processor = hf_processor.image_processor

        if videos := mm_data.pop("videos", []):
            bos_token_id = tokenizer.bos_token_id or tokenizer.eos_token_id

            pixel_values_videos_lst = []
            video_token_pooling_lst = []
            video_num_crops_lst = []
            video_num_pooled_patches_lst = []
            video_num_patches_lst = []
            video_tokens_lst = []
            num_video_tokens_lst = []

            for item in videos:
                video_array, metadata = item

                # NOTE: metadata.frames_indices indicates
                # the sampled frames indices of pre-sampled videos, which is
                # used to calculate the timestamps. Make sure that
                # do_sample_frames in mm_kwargs is false for presampled videos.

                # NOTE: a copy of mm_kwargs is created to update do_sample_frames,
                # otherwise mm_hash for the object will be incorrect.
                video_mm_kwargs = dict(**mm_kwargs)
                if "do_sample_frames" not in video_mm_kwargs:
                    # molmo_utils already has "do_sample_frames" in
                    # mm_kwargs, don't overwrite it.
                    video_mm_kwargs["do_sample_frames"] = metadata.get(
                        "do_sample_frames", False
                    )

                metadata = VideoMetadata(
                    **{k: metadata[k] for k in metadata if k != "do_sample_frames"}
                )

                video_mm_data = dict()
                video_mm_data["videos"] = [[video_array]]
                video_mm_data["video_metadata"] = [[metadata]]

                video_outputs = self.info.ctx.call_hf_processor(
                    patched_call,
                    dict(text=VIDEO_PROMPT, **video_mm_data),
                    dict(**video_mm_kwargs, **tok_kwargs),
                )

                input_ids = video_outputs.pop("input_ids")
                if input_ids[0, 0] == bos_token_id:
                    input_ids = input_ids[:, 1:]

                video_string = tokenizer.batch_decode(input_ids)[0]
                prompt = prompt.replace(VIDEO_PROMPT, video_string, 1)

                video_grids = video_outputs.pop("video_grids")
                assert video_grids[:, 0].sum() == len(
                    video_outputs["pixel_values_videos"]
                )

                video_outputs["video_num_crops"] = video_grids[:, 0]
                video_outputs["video_num_pooled_patches"] = video_grids.prod(dim=1)
                n_patches = video_outputs["pixel_values_videos"].shape[1]
                video_outputs["video_num_patches"] = (
                    video_outputs["video_num_crops"] * n_patches
                )
                (video_outputs["video_tokens"], video_outputs["num_video_tokens"]) = (
                    build_flat_video_bool_length(video_grids, hf_config)
                )

                pixel_values_videos_lst.append(video_outputs["pixel_values_videos"])
                video_token_pooling_lst.append(video_outputs["video_token_pooling"])
                video_num_crops_lst.append(video_outputs["video_num_crops"])
                video_num_pooled_patches_lst.append(
                    video_outputs["video_num_pooled_patches"]
                )
                video_num_patches_lst.append(video_outputs["video_num_patches"])
                video_tokens_lst.append(video_outputs["video_tokens"])
                num_video_tokens_lst.append(video_outputs["num_video_tokens"])

            all_video_outputs = dict(
                pixel_values_videos=torch.cat(pixel_values_videos_lst),
                video_token_pooling=torch.cat(video_token_pooling_lst),
                video_num_crops=torch.cat(video_num_crops_lst),
                video_num_pooled_patches=torch.cat(video_num_pooled_patches_lst),
                video_num_patches=torch.cat(video_num_patches_lst),
                video_tokens=torch.cat(video_tokens_lst),
                num_video_tokens=torch.cat(num_video_tokens_lst),
            )
        else:
            all_video_outputs = dict()

        processed_outputs = self.info.ctx.call_hf_processor(
            patched_call,
            dict(text=prompt, **mm_data),
            dict(**mm_kwargs, **tok_kwargs),
        )

        if (images := mm_data.get("images")) is not None:
            mm_items = self.info.parse_mm_data({"image": images}, validate=False)
            parsed_images = mm_items.get_items("image", ImageProcessorItems)
            image_sizes = [
                parsed_images.get_image_size(i) for i in range(len(parsed_images))
            ]

            # For each image: tiling_h * tiling_w + global view
            tilings = [
                self.info.select_tiling(
                    image_width=image_size.width,
                    image_height=image_size.height,
                    image_processor=image_processor,
                )
                for image_size in image_sizes
            ]
            num_crops = torch.tensor(tilings).prod(-1) + 1
            assert sum(num_crops) == len(processed_outputs["pixel_values"])
            assert sum(num_crops) == processed_outputs["image_num_crops"].sum().item()

            image_grids = processed_outputs.pop("image_grids")
            image_num_pooled_patches = image_grids[:, :2].prod(dim=1) + image_grids[
                :, 2:
            ].prod(dim=1)

            processed_outputs["image_num_pooled_patches"] = image_num_pooled_patches
            n_patches = processed_outputs["pixel_values"].shape[1]
            processed_outputs["image_num_patches"] = (
                processed_outputs["image_num_crops"] * n_patches
            )
            (
                processed_outputs["image_tokens"],
                processed_outputs["num_image_tokens"],
            ) = build_flat_image_bool_length(image_grids, hf_config)

        return BatchFeature({**processed_outputs, **all_video_outputs})