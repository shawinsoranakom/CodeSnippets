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
        crop_to_patches: bool = False,
        min_patches: int = 1,
        max_patches: int = 12,
        **kwargs,
    ) -> BatchFeature:
        num_patches = []
        processed_images = []

        for image in images:
            if crop_to_patches and max_patches > 1:
                patches = self.crop_image_to_patches(
                    image,
                    min_patches,
                    max_patches,
                    patch_size=size,
                    resample=resample,
                )
                num_patches.append(len(patches))
                # Normalize and rescale patches
                for patch in patches:
                    if do_rescale:
                        patch = self.rescale(patch, rescale_factor)
                    if do_normalize:
                        patch = self.normalize(patch, image_mean, image_std)
                    processed_images.append(patch)
            else:
                num_patches.append(1)
                if do_resize:
                    image = self.resize(image, size, resample)
                if do_rescale:
                    image = self.rescale(image, rescale_factor)
                if do_normalize:
                    image = self.normalize(image, image_mean, image_std)
                processed_images.append(image)

        return BatchFeature(
            data={"pixel_values": processed_images, "num_patches": num_patches}, tensor_type=return_tensors
        )