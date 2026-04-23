def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        image_grid_pinpoints: list[list[int]],
        resample: "PILImageResampling | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """Custom preprocessing for LLaVA-NeXT with patch processing."""
        processed_images = []
        image_sizes = []

        # Backend's resize method handles resample conversion, so we can pass it directly
        # Determine the size tuple
        if size and size.height and size.width:
            size_tuple = (size.height, size.width)
        else:
            size_tuple = (size.shortest_edge, size.shortest_edge)

        # Determine the patch size
        if crop_size and crop_size.height:
            patch_size = crop_size.height
        elif size and size.height:
            patch_size = size.height
        else:
            patch_size = size.shortest_edge

        for image in images:
            # convert image into a list of patches
            # we intentionally use the same data format as the input data format
            image_patches = self.get_image_patches(
                image,
                image_grid_pinpoints,
                size=size_tuple,
                patch_size=patch_size,
                resample=resample,
            )

            # preprocess patches
            pixel_values = []
            for patch in image_patches:
                if do_resize:
                    patch = self.resize(image=patch, size=size, resample=resample)

                if do_center_crop:
                    patch = self.center_crop(image=patch, size=crop_size)

                if do_rescale:
                    patch = self.rescale(image=patch, scale=rescale_factor)

                if do_normalize:
                    patch = self.normalize(image=patch, mean=image_mean, std=image_std)

                pixel_values.append(patch)

            pixel_values = np.array(pixel_values)
            processed_images.append(pixel_values)
            image_sizes.append(image.shape[-2:])

        if do_pad:
            processed_images = self._pad_for_batching(processed_images)

        return BatchFeature(
            data={"pixel_values": processed_images, "image_sizes": image_sizes}, tensor_type=return_tensors
        )