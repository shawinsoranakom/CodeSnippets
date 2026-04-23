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
        if input_points is not None:
            if len(original_sizes) != len(input_points):
                input_points = [
                    self._normalize_coordinates(self.target_size, point, original_sizes[0]) for point in input_points
                ]
            else:
                input_points = [
                    self._normalize_coordinates(self.target_size, point, original_size)
                    for point, original_size in zip(input_points, original_sizes)
                ]
            # check that all arrays have the same shape
            if not all(point.shape == input_points[0].shape for point in input_points):
                if input_labels is not None:
                    input_points, input_labels = self._pad_points_and_labels(
                        input_points, input_labels, point_pad_value
                    )

            input_points = np.array(input_points)

        if input_labels is not None:
            input_labels = np.array(input_labels)

        if input_boxes is not None:
            if len(original_sizes) != len(input_boxes):
                input_boxes = [
                    self._normalize_coordinates(self.target_size, box, original_sizes[0], is_bounding_box=True)
                    for box in input_boxes
                ]
            else:
                input_boxes = [
                    self._normalize_coordinates(self.target_size, box, original_size, is_bounding_box=True)
                    for box, original_size in zip(input_boxes, original_sizes)
                ]
            input_boxes = np.array(input_boxes)

        if input_boxes is not None:
            if return_tensors == "pt":
                input_boxes = torch.from_numpy(input_boxes)
                # boxes batch size of 1 by default
                input_boxes = input_boxes.unsqueeze(1) if len(input_boxes.shape) != 3 else input_boxes
            encoding_image_processor.update({"input_boxes": input_boxes})
        if input_points is not None:
            if return_tensors == "pt":
                input_points = torch.from_numpy(input_points)
                # point batch size of 1 by default
                input_points = input_points.unsqueeze(1) if len(input_points.shape) != 4 else input_points
            encoding_image_processor.update({"input_points": input_points})
        if input_labels is not None:
            if return_tensors == "pt":
                input_labels = torch.from_numpy(input_labels)
                # point batch size of 1 by default
                input_labels = input_labels.unsqueeze(1) if len(input_labels.shape) != 3 else input_labels
            encoding_image_processor.update({"input_labels": input_labels})

        return encoding_image_processor