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
        do_thumbnail: bool = True,
        do_align_long_axis: bool = False,
        **kwargs,
    ) -> BatchFeature:
        """Custom preprocessing for Donut."""
        processed_images = []
        for image in images:
            if do_align_long_axis:
                image = self.align_long_axis(image, size)
            if do_resize:
                shortest_edge = min(size.height, size.width)
                image = self.resize(image, SizeDict(shortest_edge=shortest_edge), resample)
            if do_thumbnail:
                image = self.thumbnail(image, size, resample)
            if do_pad:
                image = self.pad_image(image, size, random_padding=False)
            if do_center_crop:
                image = self.center_crop(image, crop_size)
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)