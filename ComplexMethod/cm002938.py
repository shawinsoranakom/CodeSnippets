def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        return_tensors: str | TensorType | None,
        do_align_long_axis: bool = False,
        do_thumbnail: bool = True,
        do_crop_margin: bool = True,
        do_pad: bool | None = None,
        **kwargs,
    ) -> BatchFeature:
        processed_images = []
        for image in images:
            if do_crop_margin:
                image = self.crop_margin(image)
            if do_align_long_axis:
                image = self.align_long_axis(image, size)
            if do_resize:
                image = self.resize(image, size, resample)
            if do_thumbnail:
                image = self.thumbnail(image, size)
            if do_pad:
                image = self.pad_images(image, size)
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)