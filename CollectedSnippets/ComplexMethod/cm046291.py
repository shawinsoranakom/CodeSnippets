def forward(self, im: torch.Tensor) -> list[np.ndarray]:
        """Run Google TensorFlow inference with format-specific execution and output post-processing.

        Args:
            im (torch.Tensor): Input image tensor in BHWC format (converted from BCHW by AutoBackend).

        Returns:
            (list[np.ndarray]): Model predictions as a list of numpy arrays.
        """
        im = im.cpu().numpy()
        if self.format == "saved_model":
            y = self.model.serving_default(im)
            if not isinstance(y, list):
                y = [y]
        elif self.format == "pb":
            import tensorflow as tf

            y = self.frozen_func(x=tf.constant(im))
        else:
            h, w = im.shape[1:3]

            details = self.input_details[0]
            is_int = details["dtype"] in {np.int8, np.int16}

            if is_int:
                scale, zero_point = details["quantization"]
                im = (im / scale + zero_point).astype(details["dtype"])

            self.interpreter.set_tensor(details["index"], im)
            self.interpreter.invoke()

            y = []
            for output in self.output_details:
                x = self.interpreter.get_tensor(output["index"])
                if is_int:
                    scale, zero_point = output["quantization"]
                    x = (x.astype(np.float32) - zero_point) * scale
                if x.ndim == 3:
                    # Denormalize xywh by image size
                    if x.shape[-1] == 6 or self.end2end:
                        x[:, :, [0, 2]] *= w
                        x[:, :, [1, 3]] *= h
                        if self.task == "pose":
                            x[:, :, 6::3] *= w
                            x[:, :, 7::3] *= h
                    else:
                        x[:, [0, 2]] *= w
                        x[:, [1, 3]] *= h
                        if self.task == "pose":
                            x[:, 5::3] *= w
                            x[:, 6::3] *= h
                y.append(x)

        if self.task == "segment":  # segment with (det, proto) output order reversed
            if len(y[1].shape) != 4:
                y = list(reversed(y))  # should be y = (1, 116, 8400), (1, 160, 160, 32)
            if y[1].shape[-1] == 6:  # end-to-end model
                y = [y[1]]
            else:
                y[1] = np.transpose(y[1], (0, 3, 1, 2))  # should be y = (1, 116, 8400), (1, 32, 160, 160)
        return [x if isinstance(x, np.ndarray) else x.numpy() for x in y]