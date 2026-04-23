def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        high_res_size: SizeDict,
        min_size: int,
        resample: "PILImageResampling | None",
        high_res_resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        high_res_image_mean: float | list[float] | None,
        high_res_image_std: float | list[float] | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        do_pad: bool = True,
        **kwargs,
    ) -> BatchFeature:
        # Group images by size for batched resizing
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        high_res_resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_high_res_images = self.resize(
                    image=stacked_images, size=high_res_size, min_size=min_size, resample=high_res_resample
                )
            high_res_resized_images_grouped[shape] = stacked_high_res_images
        high_res_resized_images = reorder_images(high_res_resized_images_grouped, grouped_images_index)

        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_high_res_images, grouped_high_res_images_index = group_images_by_shape(
            high_res_resized_images, disable_grouping=disable_grouping
        )
        high_res_padded_images = {}
        high_res_processed_images_grouped = {}
        for shape, stacked_high_res_images in grouped_high_res_images.items():
            if do_pad:
                stacked_high_res_images = self.pad_to_square(
                    stacked_high_res_images, background_color=self.high_res_background_color
                )
                high_res_padded_images[shape] = stacked_high_res_images
            # Fused rescale and normalize
            stacked_high_res_images = self.rescale_and_normalize(
                stacked_high_res_images,
                do_rescale,
                rescale_factor,
                do_normalize,
                high_res_image_mean,
                high_res_image_std,
            )
            high_res_processed_images_grouped[shape] = stacked_high_res_images
        high_res_processed_images = reorder_images(high_res_processed_images_grouped, grouped_high_res_images_index)

        resized_images_grouped = {}
        for shape, stacked_high_res_padded_images in high_res_padded_images.items():
            if do_resize:
                stacked_images = self.resize(
                    image=stacked_high_res_padded_images, size=size, min_size=min_size, resample=resample
                )
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_high_res_images_index)

        grouped_resized_images, grouped_resized_images_index = group_images_by_shape(
            resized_images, disable_grouping=disable_grouping
        )
        processed_images_grouped = {}
        for shape, stacked_images in grouped_resized_images.items():
            if do_pad:
                stacked_images = self.pad_to_square(stacked_images, background_color=self.background_color)
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images
        processed_images = reorder_images(processed_images_grouped, grouped_resized_images_index)

        return BatchFeature(
            data={"pixel_values": processed_images, "high_res_pixel_values": high_res_processed_images},
            tensor_type=return_tensors,
        )