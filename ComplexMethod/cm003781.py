def encode_inputs(
        self,
        pixel_values_list: list[np.ndarray],
        task_inputs: list[str] | None = None,
        segmentation_maps: list[np.ndarray] | None = None,
        instance_id_to_semantic_id: list[dict[int, int]] | dict[int, int] | None = None,
        ignore_index: int | None = None,
        do_reduce_labels: bool = False,
        return_tensors: str | TensorType | None = None,
    ) -> BatchFeature:
        ignore_index = self.ignore_index if ignore_index is None else ignore_index
        do_reduce_labels = self.do_reduce_labels if do_reduce_labels is None else do_reduce_labels
        if task_inputs is None:
            task_inputs = ["panoptic"]
        pixel_values_list = self._prepare_image_like_inputs(
            pixel_values_list, input_data_format=ChannelDimension.FIRST
        )
        if segmentation_maps is not None:
            segmentation_maps = self._prepare_image_like_inputs(
                images=segmentation_maps,
                expected_ndims=2,
                do_convert_rgb=False,
                input_data_format=ChannelDimension.FIRST,
            )
        pad_size = get_max_height_width(pixel_values_list, input_data_format=ChannelDimension.FIRST)
        encoded_inputs = self.pad(pixel_values_list, return_tensors=return_tensors)

        annotations = None
        if segmentation_maps is not None:
            annotations = []
            for idx, segmentation_map in enumerate(segmentation_maps):
                # Use instance2class_id mapping per image
                if isinstance(instance_id_to_semantic_id, list):
                    instance_id = instance_id_to_semantic_id[idx]
                else:
                    instance_id = instance_id_to_semantic_id

                # Squeeze channel dimension if present
                if segmentation_map.ndim == 3 and segmentation_map.shape[0] == 1:
                    segmentation_map = segmentation_map.squeeze(0)

                # Convert segmentation map to binary masks using numpy operations
                masks, classes = self.convert_segmentation_map_to_binary_masks(
                    segmentation_map, instance_id, ignore_index=ignore_index, do_reduce_labels=do_reduce_labels
                )

                annotations.append({"masks": masks, "classes": classes})

        if annotations is not None:
            mask_labels = []
            class_labels = []
            text_inputs = []
            num_class_obj = dict.fromkeys(self.metadata["class_names"], 0)

            for i, label in enumerate(annotations):
                task = task_inputs[i]

                if task == "semantic":
                    classes, masks, texts = self.get_semantic_annotations(label, num_class_obj)
                elif task == "instance":
                    classes, masks, texts = self.get_instance_annotations(label, num_class_obj)
                elif task == "panoptic":
                    classes, masks, texts = self.get_panoptic_annotations(label, num_class_obj)
                else:
                    raise ValueError(f"{task} was not expected, expected `semantic`, `instance` or `panoptic`")
                # Pad masks to max size using numpy operations
                # masks is a 3D array (num_masks, H, W), iterate to get 2D slices
                padded_masks = [
                    self._pad_image(image=mask, output_size=pad_size, constant_values=ignore_index) for mask in masks
                ]
                # Stack padded masks back into 3D array (num_masks, padded_H, padded_W)
                padded_masks = (
                    np.stack(padded_masks, axis=0) if padded_masks else np.zeros((0, *pad_size), dtype=np.float32)
                )
                mask_labels.append(padded_masks)
                class_labels.append(classes)
                text_inputs.append(texts)

            encoded_inputs["mask_labels"] = [
                torch.from_numpy(mask_label) if return_tensors == "pt" else mask_label for mask_label in mask_labels
            ]
            encoded_inputs["class_labels"] = [
                torch.from_numpy(class_label) if return_tensors == "pt" else class_label
                for class_label in class_labels
            ]
            encoded_inputs["text_inputs"] = text_inputs

        encoded_inputs["task_inputs"] = [f"the task is {task_input}" for task_input in task_inputs]
        return encoded_inputs