def _get_compiled_model(self, data):
        current_shapes = self._get_data_shapes(data)
        if (
            self.ov_compiled_model is not None
            and get_device() == self.ov_device
            and getattr(self, "ov_input_shapes", None) == current_shapes
        ):
            return self.ov_compiled_model

        # remove the previous cached compiled model if exists
        del self.ov_compiled_model

        # prepare parameterized input
        self.struct_params = self._parameterize_data(
            data, dynamic_batch_size=True
        )
        # construct OpenVINO graph during calling Keras Model
        self.struct_outputs = self(self.struct_params)

        parameters = []
        for p in tree.flatten(self.struct_params):
            parameters.append(p.output.get_node())
        results = []
        flat_struct_outputs = tree.flatten(self.struct_outputs)
        for r in flat_struct_outputs:
            results.append(ov_opset.result(r.output))

        self._n_main_outputs = len(results)

        # Include mask tensors as extra outputs so they are evaluated
        # during inference and can be propagated to y_pred.
        self._output_mask_indices = {}
        for i, out in enumerate(flat_struct_outputs):
            mask = backend.get_keras_mask(out)
            if mask is not None and isinstance(mask, OpenVINOKerasTensor):
                self._output_mask_indices[i] = len(results)
                results.append(ov_opset.result(mask.output))

        # prepare compiled model from scratch
        ov_model = ov.Model(results=results, parameters=parameters)
        self.ov_compiled_model = ov.compile_model(ov_model, get_device())
        self.ov_device = get_device()
        self.ov_input_shapes = current_shapes
        return self.ov_compiled_model