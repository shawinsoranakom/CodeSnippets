def call(self, inputs):
        is_torch_backend = backend.backend() == "torch"

        # Handle input conversion
        inputs_for_processing = inputs
        was_tf_input = isinstance(
            inputs, (tf.Tensor, tf.RaggedTensor, tf.SparseTensor)
        )

        if is_torch_backend and isinstance(inputs, torch.Tensor):
            inputs_for_processing = tf.convert_to_tensor(
                inputs.detach().cpu().numpy()
            )
        elif isinstance(inputs, (np.ndarray, list, tuple)):
            inputs_for_processing = tf.convert_to_tensor(inputs)
        elif not was_tf_input:
            inputs_for_processing = tf.convert_to_tensor(
                backend.convert_to_numpy(inputs)
            )

        output = super().call(inputs_for_processing)

        # Handle torch backend output conversion
        if is_torch_backend and isinstance(
            inputs, (torch.Tensor, np.ndarray, list, tuple)
        ):
            numpy_outputs = output.numpy()
            if self.invert:
                return [n.decode(self.encoding) for n in numpy_outputs]
            else:
                return torch.from_numpy(numpy_outputs)

        # other backends
        if not was_tf_input:
            output = backend_utils.convert_tf_tensor(output)

        return output