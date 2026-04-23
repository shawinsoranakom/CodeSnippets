def _preprocess(
        self,
        images: list["torch.Tensor"],
        segmentation_maps: Optional["torch.Tensor"],
        instance_id_to_semantic_id: dict[int, int] | None,
        do_resize: bool | None,
        size: SizeDict | None,
        pad_size: SizeDict | None,
        size_divisor: int | None,
        resample: Union["PILImageResampling", "tvF.InterpolationMode"] | None,
        do_rescale: bool | None,
        rescale_factor: float | None,
        do_normalize: bool | None,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        ignore_index: int | None,
        do_reduce_labels: bool | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        from ...image_utils import get_max_height_width

        if segmentation_maps is not None and len(images) != len(segmentation_maps):
            raise ValueError("Images and segmentation maps must have the same length.")

        # Group images by size for batched resizing
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        if segmentation_maps is not None:
            grouped_segmentation_maps, grouped_segmentation_maps_index = group_images_by_shape(
                segmentation_maps, disable_grouping=disable_grouping
            )
            resized_segmentation_maps_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(
                    image=stacked_images, size=size, size_divisor=size_divisor, resample=resample
                )
            if segmentation_maps is not None:
                stacked_segmentation_maps = grouped_segmentation_maps[shape]
                if do_resize:
                    stacked_segmentation_maps = self.resize(
                        image=stacked_segmentation_maps,
                        size=size,
                        size_divisor=size_divisor,
                        resample=tvF.InterpolationMode.NEAREST_EXACT,
                    )
            resized_images_grouped[shape] = stacked_images
            if segmentation_maps is not None:
                resized_segmentation_maps_grouped[shape] = stacked_segmentation_maps
        resized_images = reorder_images(resized_images_grouped, grouped_images_index)
        if segmentation_maps is not None:
            resized_segmentation_maps = reorder_images(
                resized_segmentation_maps_grouped, grouped_segmentation_maps_index
            )
        if pad_size is not None:
            padded_size = (pad_size.height, pad_size.width)
        else:
            padded_size = get_max_height_width(resized_images)

        if segmentation_maps is not None:
            mask_labels = []
            class_labels = []
            # Convert to list of binary masks and labels
            for idx, segmentation_map in enumerate(resized_segmentation_maps):
                if isinstance(instance_id_to_semantic_id, list):
                    instance_id = instance_id_to_semantic_id[idx]
                else:
                    instance_id = instance_id_to_semantic_id
                # Use instance2class_id mapping per image
                masks, classes = convert_segmentation_map_to_binary_masks_fast(
                    segmentation_map.squeeze(0),
                    instance_id,
                    ignore_index=ignore_index,
                    do_reduce_labels=do_reduce_labels,
                )
                mask_labels.append(masks)
                class_labels.append(classes)

        if segmentation_maps is not None:
            # group mask_labels as paired inputs and not images so as not to stack them
            grouped_images, grouped_segmentation_maps, grouped_images_index = group_images_by_shape(
                resized_images, mask_labels, disable_grouping=disable_grouping
            )
            processed_segmentation_maps_grouped = {}
        else:
            grouped_images, grouped_images_index = group_images_by_shape(
                resized_images, disable_grouping=disable_grouping
            )
        processed_images_grouped = {}
        processed_pixel_masks_grouped = {}
        for shape, stacked_images in grouped_images.items():
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            padded_images, pixel_masks, padded_segmentation_maps = self.pad(
                images=stacked_images,
                segmentation_maps=grouped_segmentation_maps[shape] if segmentation_maps is not None else None,
                padded_size=padded_size,
                ignore_index=ignore_index,
            )
            processed_images_grouped[shape] = padded_images
            processed_pixel_masks_grouped[shape] = pixel_masks
            if segmentation_maps is not None:
                processed_segmentation_maps_grouped[shape] = padded_segmentation_maps

        processed_images = reorder_images(processed_images_grouped, grouped_images_index)
        processed_pixel_masks = reorder_images(processed_pixel_masks_grouped, grouped_images_index)
        encoded_inputs = BatchFeature(
            data={"pixel_values": processed_images, "pixel_mask": processed_pixel_masks},
            tensor_type=return_tensors,
        )
        if segmentation_maps is not None:
            mask_labels = reorder_images(processed_segmentation_maps_grouped, grouped_images_index)
            # we cannot batch them since they don't share a common class size
            encoded_inputs["mask_labels"] = mask_labels
            encoded_inputs["class_labels"] = class_labels

        return encoded_inputs