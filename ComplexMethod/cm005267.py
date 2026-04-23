def __call__(
        self,
        images: ImageInput | None = None,
        segmentation_maps: ImageInput | None = None,
        input_points: list[list[list[list[float]]]] | torch.Tensor | None = None,
        input_labels: list[list[list[int]]] | torch.Tensor | None = None,
        input_boxes: list[list[list[float]]] | torch.Tensor | None = None,
        original_sizes: list[list[float]] | torch.Tensor | None = None,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchEncoding:
        r"""
        segmentation_maps (`ImageInput`, *optional*):
            The segmentation maps to process.
        input_points (`list[list[list[list[float]]]]`, `torch.Tensor`, *optional*):
            The points to add to the frame.
        input_labels (`list[list[list[int]]]`, `torch.Tensor`, *optional*):
            The labels for the points.
        input_boxes (`list[list[list[float]]]`, `torch.Tensor`, *optional*):
            The bounding boxes to add to the frame.
        original_sizes (`list[list[float]]`, `torch.Tensor`, *optional*):
            The original sizes of the images.

        Returns:
            A [`BatchEncoding`] with the following fields:
            - `pixel_values` (`torch.Tensor`): The processed image(s).
            - `original_sizes` (`list[list[float]]`): The original sizes of the images.
            - `labels` (`torch.Tensor`): The processed segmentation maps (if provided).
            - `input_points` (`torch.Tensor`): The processed points.
            - `input_labels` (`torch.Tensor`): The processed labels.
            - `input_boxes` (`torch.Tensor`): The processed bounding boxes.
        """
        if images is not None:
            encoding_image_processor = self.image_processor(
                images,
                segmentation_maps=segmentation_maps,
                return_tensors=return_tensors,
                **kwargs,
            )
        elif original_sizes is not None:
            if isinstance(original_sizes, torch.Tensor):
                original_sizes = original_sizes.cpu().tolist()
            encoding_image_processor = BatchEncoding({"original_sizes": original_sizes}, tensor_type=return_tensors)
        else:
            raise ValueError("Either images or original_sizes must be provided")

        # pop arguments that are not used in the forward but used nevertheless
        original_sizes = encoding_image_processor["original_sizes"]
        # Check original_sizes is of length 1 or len(images)
        if images is not None and len(original_sizes) != 1 and len(original_sizes) != len(images):
            raise ValueError(
                "original_sizes must be of length 1 or len(images). If you are passing a single image, you must pass a single original_size."
            )

        # Process input points, labels, and boxes if provided
        if input_points is not None or input_labels is not None or input_boxes is not None:
            # Validate and convert inputs to standardized format
            processed_points = self._validate_single_input(
                input_points,
                expected_depth=4,
                input_name="points",
                expected_format="[image level, object level, point level, point coordinates]",
                expected_coord_size=2,
            )
            processed_labels = self._validate_single_input(
                input_labels,
                expected_depth=3,
                input_name="labels",
                expected_format="[image level, object level, point level]",
            )
            processed_boxes = self._validate_single_input(
                input_boxes,
                expected_depth=3,
                input_name="boxes",
                expected_format="[image level, box level, box coordinates]",
                expected_coord_size=4,
            )

            # Get padding requirements for all inputs
            if processed_points is not None:
                points_max_dims = self._get_nested_dimensions(processed_points)[:3]
            if processed_labels is not None:
                labels_max_dims = self._get_nested_dimensions(processed_labels)[:3]
            if processed_boxes is not None:
                boxes_max_dims = self._get_nested_dimensions(processed_boxes)[:2]

            # Ensure points and labels have consistent dimensions
            if processed_points is not None and processed_labels is not None:
                if points_max_dims != labels_max_dims:
                    raise ValueError(
                        "Input points and labels have inconsistent dimensions. Please ensure they have the same dimensions."
                    )

            # Check that boxes don't need padding (model limitation)
            if processed_boxes is not None and len(processed_boxes) >= 2:
                if any(len(img_boxes) < boxes_max_dims[1] for img_boxes in processed_boxes):
                    raise ValueError(
                        "Input boxes have inconsistent dimensions that would require padding, "
                        "but boxes cannot be padded due to model limitations. "
                        "Please ensure all images have the same number of boxes."
                    )

            # Pad and normalize all inputs to final tensor format
            if processed_points is not None:
                padded_points = self._pad_nested_list(processed_points, points_max_dims + [2])
                final_points = torch.tensor(padded_points, dtype=torch.float32)
                self._normalize_tensor_coordinates(final_points, original_sizes, preserve_padding=True)
                encoding_image_processor.update({"input_points": final_points})

            if processed_labels is not None:
                padded_labels = self._pad_nested_list(processed_labels, labels_max_dims)
                final_labels = torch.tensor(padded_labels, dtype=torch.int64)
                encoding_image_processor.update({"input_labels": final_labels})

            if processed_boxes is not None:
                final_boxes = torch.tensor(processed_boxes, dtype=torch.float32)
                self._normalize_tensor_coordinates(final_boxes, original_sizes, is_bounding_box=True)
                encoding_image_processor.update({"input_boxes": final_boxes})

        return encoding_image_processor