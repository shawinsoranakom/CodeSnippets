def _normalize_and_convert(
        self,
        encoding_image_processor,
        original_sizes,
        input_points=None,
        input_labels=None,
        input_boxes=None,
        return_tensors="pt",
        point_pad_value=-10,
    ):
        """
        Normalize and convert the image processor output to the expected format.
        """
        # Process input points
        if input_points is not None:
            input_points = self._normalize_batch_coordinates(input_points, original_sizes)

            if not all(point.shape == input_points[0].shape for point in input_points):
                if input_labels is not None:
                    input_points, input_labels = self._pad_points_and_labels(
                        input_points, input_labels, point_pad_value
                    )

            input_points = np.array(input_points)

        # Process input labels
        if input_labels is not None:
            input_labels = np.array(input_labels)

        # Process input boxes
        if input_boxes is not None:
            input_boxes = self._normalize_batch_coordinates(input_boxes, original_sizes, is_bounding_box=True)
            input_boxes = np.array(input_boxes)

        # Update processor with converted inputs
        if input_boxes is not None:
            encoding_image_processor["input_boxes"] = self._to_tensor(input_boxes, 3, return_tensors)
        if input_points is not None:
            encoding_image_processor["input_points"] = self._to_tensor(input_points, 4, return_tensors)
        if input_labels is not None:
            encoding_image_processor["input_labels"] = self._to_tensor(input_labels, 3, return_tensors)

        return encoding_image_processor