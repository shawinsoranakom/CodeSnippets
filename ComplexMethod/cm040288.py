def _log_weight_as_image(self, weight, weight_name, epoch):
        """Logs a weight as a TensorBoard image."""
        w_img = ops.squeeze(weight)
        shape = w_img.shape
        if len(shape) == 1:  # Bias case
            w_img = ops.reshape(w_img, [1, shape[0], 1, 1])
        elif len(shape) == 2:  # Dense layer kernel case
            if shape[0] > shape[1]:
                w_img = ops.transpose(w_img)
                shape = w_img.shape
            w_img = ops.reshape(w_img, [1, shape[0], shape[1], 1])
        elif len(shape) == 3:  # ConvNet case
            if backend.image_data_format() == "channels_last":
                # Switch to channels_first to display every kernel as a separate
                # image.
                w_img = ops.transpose(w_img, [2, 0, 1])
                shape = w_img.shape
            w_img = ops.reshape(w_img, [shape[0], shape[1], shape[2], 1])

        w_img = backend.convert_to_numpy(w_img)
        shape = w_img.shape
        # Not possible to handle 3D convnets etc.
        if len(shape) == 4 and shape[-1] in [1, 3, 4]:
            self.summary.image(weight_name, w_img, step=epoch)