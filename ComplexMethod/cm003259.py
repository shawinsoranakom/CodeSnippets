def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        do_grayscale: bool = True,
        **kwargs,
    ) -> BatchFeature:
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        processed_images_grouped = {}

        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(stacked_images, size=size, resample=resample)
            processed_images_grouped[shape] = stacked_images
        resized_images = reorder_images(processed_images_grouped, grouped_images_index)

        grouped_images, grouped_images_index = group_images_by_shape(resized_images, disable_grouping=disable_grouping)
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_rescale:
                stacked_images = self.rescale(stacked_images, rescale_factor)
            if do_grayscale:
                stacked_images = convert_to_grayscale(stacked_images)
            processed_images_grouped[shape] = stacked_images

        processed_images = reorder_images(processed_images_grouped, grouped_images_index)

        # Convert back to pairs format
        image_pairs = [processed_images[i : i + 2] for i in range(0, len(processed_images), 2)]

        # Stack each pair into a single tensor to match slow processor format
        stacked_pairs = [torch.stack(pair, dim=0) for pair in image_pairs]

        # Return in same format as slow processor

        return BatchFeature(data={"pixel_values": stacked_pairs}, tensor_type=return_tensors)