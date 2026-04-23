def transform_images(self, images, transformation=None, training=True):
        inputs = self.backend.cast(images, self.compute_dtype)
        inputs_shape = self.backend.shape(inputs)

        if self.data_format == "channels_first":
            init_height = inputs_shape[-2]
            init_width = inputs_shape[-1]
        else:
            init_height = inputs_shape[-3]
            init_width = inputs_shape[-2]

        # All these operations work both with ints (static sizes) and scalar
        # tensors (dynamic sizes).
        h_diff = init_height - self.height
        w_diff = init_width - self.width

        h_start = h_diff // 2
        w_start = w_diff // 2

        if (not isinstance(h_diff, int) or h_diff >= 0) and (
            not isinstance(w_diff, int) or w_diff >= 0
        ):
            if len(inputs.shape) == 4:
                if self.data_format == "channels_first":
                    return inputs[
                        :,
                        :,
                        h_start : h_start + self.height,
                        w_start : w_start + self.width,
                    ]
                return inputs[
                    :,
                    h_start : h_start + self.height,
                    w_start : w_start + self.width,
                    :,
                ]
            elif len(inputs.shape) == 3:
                if self.data_format == "channels_first":
                    return inputs[
                        :,
                        h_start : h_start + self.height,
                        w_start : w_start + self.width,
                    ]
                return inputs[
                    h_start : h_start + self.height,
                    w_start : w_start + self.width,
                    :,
                ]
        return image_utils.smart_resize(
            inputs,
            [self.height, self.width],
            data_format=self.data_format,
            backend_module=self.backend,
        )