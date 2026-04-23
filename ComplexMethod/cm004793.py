def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        do_reduce_labels: bool,
        keep_aspect_ratio: bool,
        ensure_multiple_of: int,
        size_divisor: int | None = None,
        **kwargs,
    ) -> np.ndarray:
        """Custom preprocessing for DPT."""
        processed_images = []
        for image in images:
            if do_reduce_labels:
                image = self.reduce_label(image)
            if do_resize:
                image = self.resize(
                    image, size, resample, ensure_multiple_of=ensure_multiple_of, keep_aspect_ratio=keep_aspect_ratio
                )
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            if do_pad and size_divisor is not None:
                image = self.pad_image(image, size_divisor)
            processed_images.append(image)
        return processed_images