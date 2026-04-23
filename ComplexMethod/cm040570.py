def compute_output_spec(self, images):
        images_shape = list(images.shape)

        if self.data_format == "channels_last":
            height_axis, width_axis = -3, -2
        else:
            height_axis, width_axis = -2, -1
        height, width = images_shape[height_axis], images_shape[width_axis]

        if height is None and self.target_height is None:
            raise ValueError(
                "When the height of the images is unknown, `target_height` "
                "must be specified."
                f"Received images.shape={images_shape} and "
                f"target_height={self.target_height}"
            )
        if width is None and self.target_width is None:
            raise ValueError(
                "When the width of the images is unknown, `target_width` "
                "must be specified."
                f"Received images.shape={images_shape} and "
                f"target_width={self.target_width}"
            )

        target_height = self.target_height
        if target_height is None:
            target_height = height - self.top_cropping - self.bottom_cropping
        target_width = self.target_width
        if target_width is None:
            target_width = width - self.left_cropping - self.right_cropping

        images_shape[height_axis] = target_height
        images_shape[width_axis] = target_width
        return KerasTensor(shape=images_shape, dtype=images.dtype)