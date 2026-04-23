def _expand_dict_for_generation_visual(dict_to_expand):
            image_grid_thw = model_kwargs.get("image_grid_thw", None)
            video_grid_thw = model_kwargs.get("video_grid_thw", None)
            video_merge_sizes = model_kwargs.get("video_merge_sizes", None)
            video_compression_mask = model_kwargs.get("video_compression_mask", None)

            image_nums, video_nums = self._get_image_nums_and_video_nums(
                input_ids,
                inputs_embeds=model_kwargs.get("inputs_embeds", None),
                image_grid_thw=image_grid_thw,
                image_merge_sizes=model_kwargs.get("image_merge_sizes", None),
                video_grid_thw=video_grid_thw,
                video_merge_sizes=video_merge_sizes,
                video_compression_mask=video_compression_mask,
            )
            for key in dict_to_expand:
                if key == "pixel_values":
                    # split images into samples
                    samples = torch.split(image_grid_thw, list(image_nums))
                    # compute the sequence length of images for each sample
                    lengths = [torch.prod(sample, dim=1).sum() for sample in samples]
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "image_grid_thw":
                    # get the num of images for each sample
                    lengths = list(image_nums)
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "image_merge_sizes":
                    lengths = list(image_nums)
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "pixel_values_videos":
                    samples = torch.split(video_grid_thw, list(video_nums))
                    lengths = [torch.prod(sample, dim=1).sum() for sample in samples]
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "video_compression_mask":
                    samples = torch.split(video_grid_thw, list(video_nums))
                    merge_sizes = torch.split(video_merge_sizes, list(video_nums))
                    lengths = [
                        (torch.prod(sample, dim=1) // merge_size**2).sum()
                        for sample, merge_size in zip(samples, merge_sizes)
                    ]
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "video_grid_thw":
                    lengths = list(video_nums)
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )
                elif key == "video_merge_sizes":
                    lengths = list(video_nums)
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                    )

            return dict_to_expand