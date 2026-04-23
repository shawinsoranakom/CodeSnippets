def call(self, data, training=True):
        transformation = self.get_random_transformation(data, training=training)
        if isinstance(data, dict):
            is_batched = self._is_batched(data["images"])
            if is_batched:
                data["images"] = self.transform_images(
                    self.backend.convert_to_tensor(data["images"]),
                    transformation=transformation,
                    training=training,
                )
            else:
                data["images"] = self.transform_single_image(
                    self.backend.convert_to_tensor(data["images"]),
                    transformation=transformation,
                    training=training,
                )
            if "bounding_boxes" in data:
                if not self.bounding_box_format:
                    raise ValueError(
                        "You passed an input with a 'bounding_boxes' key, "
                        "but you didn't specify a bounding box format. "
                        "Pass a `bounding_box_format` argument to your "
                        f"{self.__class__.__name__} layer, e.g. "
                        "`bounding_box_format='xyxy'`."
                    )
                bounding_boxes = densify_bounding_boxes(
                    data["bounding_boxes"],
                    is_batched=is_batched,
                    backend=self.backend,
                )

                if is_batched:
                    data["bounding_boxes"] = self.transform_bounding_boxes(
                        bounding_boxes,
                        transformation=transformation,
                        training=training,
                    )
                else:
                    data["bounding_boxes"] = self.transform_single_bounding_box(
                        bounding_boxes,
                        transformation=transformation,
                        training=training,
                    )
            if "labels" in data:
                if is_batched:
                    data["labels"] = self.transform_labels(
                        self.backend.convert_to_tensor(data["labels"]),
                        transformation=transformation,
                        training=training,
                    )
                else:
                    data["labels"] = self.transform_single_label(
                        self.backend.convert_to_tensor(data["labels"]),
                        transformation=transformation,
                        training=training,
                    )
            if "segmentation_masks" in data:
                if is_batched:
                    data["segmentation_masks"] = (
                        self.transform_segmentation_masks(
                            data["segmentation_masks"],
                            transformation=transformation,
                            training=training,
                        )
                    )
                else:
                    data["segmentation_masks"] = (
                        self.transform_single_segmentation_mask(
                            data["segmentation_masks"],
                            transformation=transformation,
                            training=training,
                        )
                    )
            return data

        # `data` is just images.
        if self._is_batched(data):
            return self.transform_images(
                self.backend.convert_to_tensor(data),
                transformation=transformation,
                training=training,
            )
        return self.transform_single_image(
            self.backend.convert_to_tensor(data),
            transformation=transformation,
            training=training,
        )