def preprocess_multidata(
        self,
        images: PIL.Image.Image | list[PIL.Image.Image] | None = None,
        video: list[PIL.Image.Image] | np.ndarray | None = None,
        do_convert_rgb: bool | None = True,
        min_pixels: int = MIN_PIXELS,
        max_pixels: int = MAX_PIXELS,
        return_tensors: str | None = "pt",
    ):
        is_video = False
        if images is not None:
            if not isinstance(images, list):
                images = [images]
        elif video is not None:
            is_video = True
            # type of video in dummy_mm_data is np.ndarray
            if isinstance(video, np.ndarray):
                images = []
                for i in range(video.shape[0]):
                    image = PIL.Image.fromarray(video[i].astype(np.uint8))
                    images.append(image)
            elif isinstance(video, list):
                images = video
        else:
            raise ValueError("Either images or video should be provided.")
        assert images is not None
        min_pixels = min(
            max_pixels if max_pixels is not None else MAX_PIXELS,
            min_pixels if min_pixels is not None else MIN_PIXELS,
        )
        images = [
            image.convert("RGB") if do_convert_rgb and image.mode != "RGB" else image
            for image in images
        ]

        width, height = images[0].size
        resized_height, resized_width = height, width
        processed_images = []
        for image in images:
            resized_height, resized_width = self.smart_resize(
                height,
                width,
                factor=self.patch_size * self.hidden_stride,
                min_pixels=min_pixels,
                max_pixels=max_pixels,
            )
            new_size = dict(height=resized_height, width=resized_width)
            image_pt = self.image_processor.preprocess(image, size=new_size)[
                "pixel_values"
            ][0]

            processed_images.append(image_pt)

        patches = np.array(processed_images)
        if patches.shape[0] % self.temporal_patch_size != 0:
            num_to_pad = self.temporal_patch_size - (
                patches.shape[0] % self.temporal_patch_size
            )
            repeats = np.repeat(patches[-1][np.newaxis], num_to_pad, axis=0)
            patches = np.concatenate([patches, repeats], axis=0)
        channel = patches.shape[1]
        grid_t = patches.shape[0] // self.temporal_patch_size
        grid_h = resized_height // self.patch_size
        grid_w = resized_width // self.patch_size

        patches = patches.reshape(
            grid_t,
            self.temporal_patch_size,
            channel,
            grid_h // self.hidden_stride,
            self.hidden_stride,
            self.patch_size,
            grid_w // self.hidden_stride,
            self.hidden_stride,
            self.patch_size,
        )
        patches = patches.transpose(0, 3, 6, 4, 7, 2, 1, 5, 8)
        flatten_patches = patches.reshape(
            grid_t * grid_h * grid_w,
            channel * self.temporal_patch_size * self.patch_size * self.patch_size,
        )

        visual_placeholders = self.construct_visual_placeholders(
            [grid_t, grid_h, grid_w], is_video
        )
        return (
            torch.tensor(flatten_patches),
            visual_placeholders,
            torch.tensor([[grid_t, grid_h, grid_w]]),
        )