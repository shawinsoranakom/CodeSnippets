def _preprocess(
        self,
        images: list[np.ndarray],
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        return_tensors: str | TensorType | None,
        max_image_size: int = 980,
        min_image_size: int = 336,
        split_resolutions: list[list[int]] | None = None,
        split_image: bool = False,
        resample: "PILImageResampling | None" = None,
        **kwargs,
    ) -> BatchFeature:
        if max_image_size not in [490, 980]:
            raise ValueError("max_image_size must be either 490 or 980")

        pixel_values = []
        pixel_masks = []
        num_crops = None

        for image in images:
            if split_image:
                crop_images = self.get_image_patches(image, split_resolutions, max_image_size, resample)
            else:
                crop_images = [image]

            if num_crops is None or len(crop_images) > num_crops:
                num_crops = len(crop_images)

            for crop_image in crop_images:
                h, w = crop_image.shape[-2], crop_image.shape[-1]
                scale = max_image_size / max(h, w)
                if w >= h:
                    new_h = max(int(h * scale), min_image_size)
                    new_w = max_image_size
                else:
                    new_h = max_image_size
                    new_w = max(int(w * scale), min_image_size)

                crop_image = self.resize(crop_image, SizeDict(height=new_h, width=new_w), resample)

                padding_bottom = max_image_size - new_h
                padding_right = max_image_size - new_w
                crop_image = np.pad(
                    crop_image, ((0, 0), (0, padding_bottom), (0, padding_right)), mode="constant", constant_values=0
                )

                pixel_mask = np.zeros((max_image_size, max_image_size), dtype=bool)
                pixel_mask[:new_h, :new_w] = True
                pixel_masks.append(pixel_mask)

                if do_rescale:
                    crop_image = self.rescale(crop_image, rescale_factor)
                if do_normalize:
                    crop_image = self.normalize(crop_image, image_mean, image_std)

                pixel_values.append(crop_image)

        return BatchFeature(
            data={
                "pixel_values": np.stack(pixel_values, axis=0),
                "pixel_mask": np.stack(pixel_masks, axis=0),
                "num_crops": num_crops,
            },
            tensor_type=return_tensors,
        )