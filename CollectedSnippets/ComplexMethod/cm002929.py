def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        do_split_image: bool,
        do_pad: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        **kwargs,
    ):
        """Preprocesses the input images and masks if provided."""
        processed_images, patch_offsets = [], []

        # Resize images
        resized_images = []
        for image in images:
            if do_resize:
                image = self.resize(image, size, resample)
            resized_images.append(image)

        # Split images into patches if requested
        if do_split_image:
            for idx, img in enumerate(resized_images):
                patches, offsets = self._split_image(img, size, idx)
                processed_images.extend(patches)
                patch_offsets.extend(offsets)
            images = processed_images
        else:
            images = resized_images

        # Pad images if requested
        if do_pad:
            images = [self._pad(img, size) for img in images]

        # Rescale and normalize
        processed_images = []
        for image in images:
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        return processed_images, patch_offsets