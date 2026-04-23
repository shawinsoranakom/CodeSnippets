def _preprocess(
        self,
        images: list[np.ndarray],
        segmentation_maps: list[np.ndarray] | None,
        instance_id_to_semantic_id: dict[int, int] | None,
        do_resize: bool | None,
        size: SizeDict | None,
        pad_size: SizeDict | None,
        size_divisor: int | None,
        resample: PILImageResampling | None,
        do_rescale: bool | None,
        rescale_factor: float | None,
        do_normalize: bool | None,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        ignore_index: int | None,
        do_reduce_labels: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        if segmentation_maps is not None and len(images) != len(segmentation_maps):
            raise ValueError("Images and segmentation maps must have the same length.")

        # Process images one by one (no batching in PIL backend)
        resized_images = []
        resized_segmentation_maps = None
        if segmentation_maps is not None:
            resized_segmentation_maps = []

        for idx, image in enumerate(images):
            if do_resize:
                image = self.resize(image=image, size=size, size_divisor=size_divisor, resample=resample)
            resized_images.append(image)

            if segmentation_maps is not None:
                seg_map = segmentation_maps[idx]
                if do_resize:
                    seg_map = self.resize(
                        image=seg_map, size=size, size_divisor=size_divisor, resample=PILImageResampling.NEAREST
                    )
                resized_segmentation_maps.append(seg_map)

        # Determine padded size
        if pad_size is not None:
            padded_size = (pad_size.height, pad_size.width)
        else:
            padded_size = get_max_height_width(resized_images, input_data_format=ChannelDimension.FIRST)

        # Convert segmentation maps to binary masks if provided
        mask_labels = None
        class_labels = None
        if segmentation_maps is not None:
            mask_labels = []
            class_labels = []
            for idx, segmentation_map in enumerate(resized_segmentation_maps):
                if isinstance(instance_id_to_semantic_id, list):
                    instance_id = instance_id_to_semantic_id[idx]
                else:
                    instance_id = instance_id_to_semantic_id
                # Squeeze channel dimension if present
                if segmentation_map.ndim == 3 and segmentation_map.shape[0] == 1:
                    segmentation_map = segmentation_map.squeeze(0)
                masks, classes = convert_segmentation_map_to_binary_masks(
                    segmentation_map, instance_id, ignore_index=ignore_index, do_reduce_labels=do_reduce_labels
                )
                mask_labels.append(masks)
                class_labels.append(classes)

        # Process images: rescale, normalize, pad
        processed_images = []
        for image in resized_images:
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        # Pad images and create pixel masks (also pad mask_labels to match padded image size)
        padded_images, pixel_masks, padded_mask_labels = self.pad(
            images=processed_images,
            padded_size=padded_size,
            segmentation_maps=mask_labels,
            fill=0,
            ignore_index=ignore_index,  # Match Torchvision backend for cross-backend equivalence
        )

        encoded_inputs = BatchFeature(
            data={"pixel_values": padded_images, "pixel_mask": pixel_masks}, tensor_type=return_tensors
        )
        # we cannot batch them since they don't share a common class size
        if segmentation_maps is not None:
            encoded_inputs["mask_labels"] = [
                torch.from_numpy(mask_label) if return_tensors == "pt" else mask_label
                for mask_label in padded_mask_labels
            ]
            encoded_inputs["class_labels"] = [
                torch.from_numpy(class_label) if return_tensors == "pt" else class_label
                for class_label in class_labels
            ]

        return encoded_inputs