def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        pad_size: SizeDict | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        processed_images = []
        for image in images:
            # Apply pad_to_square first if needed (before resize)
            if do_pad:
                background_color = tuple(int(x * 255) for x in image_mean) if image_mean else 0
                image = self.pad_to_square(image, background_color=background_color)

            if do_resize:
                image = self.resize(image=image, size=size, resample=resample)

            if do_center_crop:
                image = self.center_crop(image, crop_size)

            if do_rescale:
                image = self.rescale(image, rescale_factor)

            if do_normalize:
                image = self.normalize(image, image_mean, image_std)

            processed_images.append(image)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)