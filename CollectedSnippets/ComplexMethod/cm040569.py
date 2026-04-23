def compute_output_spec(self, images):
        images_shape = list(images.shape)
        original_ndim = len(images_shape)
        if self.data_format == "channels_last":
            channels_in = images_shape[-1]
        else:
            channels_in = images_shape[-4] if self.is_3d else images_shape[-3]

        if self.is_3d:
            # 3D patch extraction
            if original_ndim == 4:
                images_shape = [1] + images_shape
            filters = self.size[0] * self.size[1] * self.size[2] * channels_in
            kernel_size = (self.size[0], self.size[1], self.size[2])
        else:
            # 2D patch extraction
            if original_ndim == 3:
                images_shape = [1] + images_shape
            filters = self.size[0] * self.size[1] * channels_in
            kernel_size = (self.size[0], self.size[1])

        out_shape = compute_conv_output_shape(
            images_shape,
            filters,
            kernel_size,
            strides=self.strides,
            padding=self.padding,
            data_format=self.data_format,
            dilation_rate=self.dilation_rate,
        )

        if self.is_3d:
            if original_ndim == 4:
                out_shape = out_shape[1:]
        else:
            if original_ndim == 3:
                out_shape = out_shape[1:]
        return KerasTensor(shape=out_shape, dtype=images.dtype)