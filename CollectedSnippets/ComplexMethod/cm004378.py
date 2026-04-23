def _preprocess(
        self,
        images: list[list[np.ndarray]],
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        padding_value: float | None,
        padding_mode: str | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> FuyuBatchFeature:
        # Process nested images one by one
        original_image_sizes = []
        processed_images = []
        for batch_images in images:
            if batch_images:
                original_image_sizes.append(batch_images[0].shape[-2:])
                processed_batch = []
                for image in batch_images:
                    if do_resize:
                        image = self.resize(image=image, size=size, resample=resample)
                    processed_batch.append(image)
                processed_images.append(processed_batch)
            else:
                processed_images.append([])

        image_sizes = [batch_image[0].shape[-2:] for batch_image in processed_images if batch_image]
        image_unpadded_heights = [[image_size[0]] for image_size in image_sizes]
        image_unpadded_widths = [[image_size[1]] for image_size in image_sizes]
        image_scale_factors = [
            [resized_size[0] / original_size[0]]
            for original_size, resized_size in zip(original_image_sizes, image_sizes)
        ]

        if do_pad:
            # Handle nested padding manually since PIL backend doesn't support is_nested
            target_height, target_width = size.height, size.width
            for batch_idx, batch_images in enumerate(processed_images):
                for img_idx, image in enumerate(batch_images):
                    from ...image_utils import ChannelDimension

                    height, width = get_image_size(image, channel_dim=ChannelDimension.FIRST)
                    padding_height = target_height - height
                    padding_width = target_width - width
                    if padding_height > 0 or padding_width > 0:
                        pad_width = ((0, 0), (0, padding_height), (0, padding_width))
                        if padding_mode == "constant":
                            image = np.pad(image, pad_width, mode="constant", constant_values=padding_value)
                        else:
                            image = np.pad(image, pad_width, mode=padding_mode)
                        processed_images[batch_idx][img_idx] = image

        # Process rescale and normalize one by one
        for batch_idx, batch_images in enumerate(processed_images):
            for img_idx, image in enumerate(batch_images):
                if do_rescale:
                    image = self.rescale(image, rescale_factor)
                if do_normalize:
                    image = self.normalize(image, image_mean, image_std)
                processed_images[batch_idx][img_idx] = image

        return FuyuBatchFeature(
            data={
                "images": processed_images,
                "image_unpadded_heights": image_unpadded_heights,
                "image_unpadded_widths": image_unpadded_widths,
                "image_scale_factors": image_scale_factors,
            },
            tensor_type=return_tensors,
        )