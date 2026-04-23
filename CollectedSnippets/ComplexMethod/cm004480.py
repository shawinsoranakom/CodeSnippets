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
        return_tensors: str | TensorType | None,
        crop_to_patches: bool = False,
        min_patches: int = 1,
        max_patches: int = 12,
        use_covering_area_grid: bool = True,
        **kwargs,
    ) -> BatchFeature:
        if crop_to_patches and max_patches > 1:
            # Crop to patches first
            processed_images = []
            grids = []
            for image in images:
                patches, grid = self.crop_image_to_patches(
                    image,
                    min_patches,
                    max_patches,
                    patch_size=size,
                    use_covering_area_grid=use_covering_area_grid,
                    resample=resample,
                )
                processed_images.extend(patches)
                grids.append(grid)
            images = processed_images
        else:
            grids = [[1, 1] for _ in range(len(images))]

        # Process all images (including patches if any) through the standard pipeline
        processed_images = []
        for image in images:
            if do_resize:
                image = self.resize(image, size=size, resample=resample)
            if do_center_crop:
                image = self.center_crop(image, crop_size)
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        return BatchFeature(data={"pixel_values": processed_images, "grids": grids}, tensor_type=return_tensors)