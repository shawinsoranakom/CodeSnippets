def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        segmentation_maps: ImageInput | None = None,
        input_boxes: list[list[list[float]]] | torch.Tensor | None = None,
        input_boxes_labels: list[list[list[int]]] | torch.Tensor | None = None,
        original_sizes: list[list[float]] | torch.Tensor | None = None,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchEncoding:
        r"""
        images (`ImageInput`, *optional*):
            The image(s) to process.
        text (`str`, `list[str]`, `list[list[str]]`, *optional*):
            The text to process.
        segmentation_maps (`ImageInput`, *optional*):
            The segmentation maps to process.
        input_boxes (`list[list[list[float]]]`, `torch.Tensor`, *optional*):
            The bounding boxes to process.
        input_boxes_labels (`list[list[int]]`, `torch.Tensor`, *optional*):
            The labels for the bounding boxes.
        original_sizes (`list[list[float]]`, `torch.Tensor`, *optional*):
            The original sizes of the images.

        Returns:
            A [`BatchEncoding`] with the following fields:
            - `pixel_values` (`torch.Tensor`): The processed image(s).
            - `original_sizes` (`list[list[float]]`): The original sizes of the images.
            - `labels` (`torch.Tensor`): The processed segmentation maps (if provided).
            - `input_boxes_labels` (`torch.Tensor`): The processed labels for the bounding boxes.
            - `input_boxes` (`torch.Tensor`): The processed bounding boxes.
        """
        encoding = None
        if images is not None:
            encoding = self.image_processor(
                images,
                segmentation_maps=segmentation_maps,
                return_tensors=return_tensors,
                **kwargs,
            )
        elif original_sizes is not None:
            if isinstance(original_sizes, torch.Tensor):
                original_sizes = original_sizes.cpu().tolist()
            encoding = BatchEncoding({"original_sizes": original_sizes}, tensor_type=return_tensors)
        elif input_boxes is not None:
            raise ValueError("Either images or original_sizes must be provided if input_boxes is not None")

        text = self._resolve_text_prompts(text, input_boxes)
        if text is not None:
            text_inputs = self.tokenizer(text, return_tensors=return_tensors, padding="max_length", max_length=32)
            if encoding is not None:
                encoding.update(text_inputs)
            else:
                encoding = text_inputs

        # Process input boxes if provided
        if input_boxes is not None:
            original_sizes = encoding["original_sizes"]
            # Validate and convert inputs to standardized format
            processed_boxes = self._validate_single_input(
                input_boxes,
                expected_depth=3,
                input_name="boxes",
                expected_format="[image level, box level, box coordinates]",
                expected_coord_size=4,
            )
            processed_boxes_labels = self._validate_single_input(
                input_boxes_labels,
                expected_depth=2,
                input_name="labels",
                expected_format="[image level, box level]",
            )

            # Auto-generate labels so padded None entries are masked out in the geometry encoder (#45059).
            if processed_boxes is not None and processed_boxes_labels is None:
                processed_boxes_labels = self._generate_default_box_labels(processed_boxes)

            # Get padding requirements for all inputs
            if processed_boxes is not None:
                boxes_max_dims = self._get_nested_dimensions(processed_boxes)[:2]
            if processed_boxes_labels is not None:
                boxes_labels_max_dims = self._get_nested_dimensions(processed_boxes_labels)[:2]

            # Ensure boxes and labels have consistent dimensions
            if processed_boxes is not None and processed_boxes_labels is not None:
                if boxes_max_dims != boxes_labels_max_dims:
                    raise ValueError(
                        "Input boxes and labels have inconsistent dimensions. Please ensure they have the same dimensions."
                    )

            # Pad and normalize all inputs to final tensor format
            if processed_boxes is not None:
                padded_boxes = self._pad_nested_list(processed_boxes, boxes_max_dims + [4])
                final_boxes = torch.tensor(padded_boxes, dtype=torch.float32)
                self._normalize_tensor_coordinates(
                    final_boxes, original_sizes, is_bounding_box=True, preserve_padding=True
                )
                final_boxes = box_xyxy_to_cxcywh(final_boxes)
                encoding.update({"input_boxes": final_boxes})

            if processed_boxes_labels is not None:
                padded_boxes_labels = self._pad_nested_list(processed_boxes_labels, boxes_labels_max_dims)
                final_boxes_labels = torch.tensor(padded_boxes_labels, dtype=torch.int64)
                encoding.update({"input_boxes_labels": final_boxes_labels})

        return encoding