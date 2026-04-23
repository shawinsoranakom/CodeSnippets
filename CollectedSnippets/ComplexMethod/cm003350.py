def _preprocess(
        self,
        images: list[list["torch.Tensor"]],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        do_image_splitting: bool | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        grouped_images, grouped_images_index = group_images_by_shape(
            images, disable_grouping=disable_grouping, is_nested=True
        )
        split_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_image_splitting:
                stacked_images = self.split_images(stacked_images)
            split_images_grouped[shape] = stacked_images
        split_images = reorder_images(split_images_grouped, grouped_images_index, is_nested=True)
        if do_image_splitting:
            for i, group_images in enumerate(split_images):
                split_images[i] = [image for sublist in group_images for image in sublist]

        grouped_images, grouped_images_index = group_images_by_shape(
            split_images, disable_grouping=disable_grouping, is_nested=True
        )
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(stacked_images, size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index, is_nested=True)

        grouped_images, grouped_images_index = group_images_by_shape(
            resized_images, disable_grouping=disable_grouping, is_nested=True
        )
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images
        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=True)

        if do_pad:
            max_num_images = max(len(images_) for images_ in processed_images)
            max_height, max_width = get_max_height_width(processed_images)

            processed_images_padded = torch.zeros(
                len(processed_images),
                max_num_images,
                *(processed_images[0][0].shape[0], max_height, max_width),
                device=processed_images[0][0].device,
            )
            pixel_attention_masks = torch.zeros(
                len(processed_images),
                max_num_images,
                *(max_height, max_width),
                device=processed_images[0][0].device,
            )
            for i, images in enumerate(processed_images):
                for j, image in enumerate(images):
                    processed_images_padded[i, j], pixel_attention_masks[i, j] = self.pad(
                        image, (max_height, max_width)
                    )
            processed_images = processed_images_padded
        if do_pad:
            data = {"pixel_values": processed_images, "pixel_attention_mask": pixel_attention_masks}
        elif return_tensors == "pt":
            data = {"pixel_values": torch.stack([torch.stack(images) for images in processed_images])}
        else:
            data = {"pixel_values": processed_images}
        return BatchFeature(data=data, tensor_type=return_tensors)