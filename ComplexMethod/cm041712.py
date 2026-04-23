def _get_mm_inputs(
        self,
        images: list["ImageInput"],
        videos: list["VideoInput"],
        audios: list["AudioInput"],
        processor: "ProcessorMixin",
        **kwargs,
    ) -> dict[str, "torch.Tensor"]:
        image_processor: BaseImageProcessor = getattr(processor, "image_processor")
        image_processor_kwargs = {}
        if getattr(processor, "crop_to_patches", False):
            image_processor_kwargs.update(
                {
                    "crop_to_patches": True,
                    "max_patches": 12,
                    "min_patches": 1,
                }
            )

        mm_inputs = {}
        image_video_patches = []

        if len(images) != 0:
            images = self._regularize_images(
                images,
                image_max_pixels=getattr(processor, "image_max_pixels", 1024 * 1024),
                image_min_pixels=getattr(processor, "image_min_pixels", 32 * 32),
            )["images"]

        if len(videos) != 0:
            videos = self._regularize_videos(
                videos,
                image_max_pixels=getattr(processor, "video_max_pixels", 256 * 256),
                image_min_pixels=getattr(processor, "video_min_pixels", 16 * 16),
                video_fps=getattr(processor, "video_fps", 2.0),
                video_maxlen=getattr(processor, "video_maxlen", 128),
            )["videos"]

        if len(images) != 0:
            images = make_flat_list_of_images(images)
            image_inputs = image_processor(images=images, return_tensors="pt", **image_processor_kwargs)
            image_num_patches = image_inputs.pop("num_patches")
            image_pixel_values = image_inputs.pop("pixel_values")
            image_num_patches_indices = np.cumsum(image_num_patches)

        if len(videos) != 0:
            videos = make_batched_videos(videos)
            num_frames_per_video = [len(video) for video in videos]
            patch_indices = np.cumsum(num_frames_per_video)
            image_processor_kwargs["crop_to_patches"] = False
            video_inputs = image_processor(images=videos, return_tensors="pt", **image_processor_kwargs)
            video_num_patches = video_inputs.pop("num_patches")
            video_pixel_values = video_inputs.pop("pixel_values")
            video_num_patches_indices = np.cumsum(video_num_patches)

        # NOT SUPPORT IMAGE VIDEO INTERLEAVED
        if len(images) != 0 and image_pixel_values is not None:
            for i in range(len(images)):
                start_index = image_num_patches_indices[i - 1] if i > 0 else 0
                end_index = image_num_patches_indices[i]
                image_video_patches.append(image_pixel_values[start_index:end_index])

        if len(videos) != 0 and video_pixel_values is not None:
            patch_indices_with_prefix = [0] + list(patch_indices)
            for i in range(len(videos)):
                current_patch_index = patch_indices_with_prefix[i]
                end_patch_index = patch_indices_with_prefix[i + 1]
                start_index = video_num_patches_indices[current_patch_index - 1] if i > 0 else 0
                end_index = video_num_patches_indices[end_patch_index - 1]
                image_video_patches.append(video_pixel_values[start_index:end_index])

        if len(images) != 0 or len(videos) != 0:
            mm_inputs["pixel_values"] = torch.cat(image_video_patches, dim=0)

        if len(images) != 0:
            mm_inputs.update({"image_num_patches": image_num_patches})

        if len(videos) != 0:
            mm_inputs.update({"video_patch_indices": patch_indices})
            mm_inputs.update({"video_num_patches": video_num_patches})

        return mm_inputs