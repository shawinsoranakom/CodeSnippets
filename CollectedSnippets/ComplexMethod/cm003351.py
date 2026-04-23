def _preprocess(
        self,
        images: list[list[np.ndarray]],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        do_image_splitting: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """Process a batch of images. Mirrors TorchvisionBackend._preprocess with per-image loops."""
        if do_image_splitting:
            new_images = []
            for batch_images in images:
                new_batch = []
                for image in batch_images:
                    new_batch.extend(self.split_images(image))
                new_images.append(new_batch)
            images = new_images

        if do_resize:
            images = [
                [self.resize(image=img, size=size, resample=resample) for img in batch_images]
                for batch_images in images
            ]

        if do_rescale:
            images = [[self.rescale(img, rescale_factor) for img in batch_images] for batch_images in images]
        if do_normalize:
            images = [[self.normalize(img, image_mean, image_std) for img in batch_images] for batch_images in images]

        if do_pad:
            max_num_images = max(len(images_) for images_ in images)
            max_height, max_width = get_max_height_width(images)
            num_channels = images[0][0].shape[0]

            padded_images_list = [
                [np.zeros((num_channels, max_height, max_width), dtype=np.float32) for _ in range(max_num_images)]
                for _ in range(len(images))
            ]
            pixel_attention_masks = [
                [np.zeros((max_height, max_width), dtype=np.int64) for _ in range(max_num_images)]
                for _ in range(len(images))
            ]

            for i, batch_images in enumerate(images):
                for j, image in enumerate(batch_images):
                    padded_images_list[i][j], pixel_attention_masks[i][j] = self.pad(image, (max_height, max_width))
            images = padded_images_list

        if do_pad:
            data = {
                "pixel_values": np.array(images),
                "pixel_attention_mask": np.array(pixel_attention_masks),
            }
        elif return_tensors == "pt":
            data = {"pixel_values": np.asarray(images)}
        else:
            data = {"pixel_values": images}

        return BatchFeature(data=data, tensor_type=return_tensors)