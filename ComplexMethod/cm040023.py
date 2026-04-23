def __call__(self, inputs, **kwargs):
        sample_input = tree.flatten(inputs)[0]
        if (
            not isinstance(sample_input, keras.KerasTensor)
            and backend_utils.in_tf_graph()
            and not jax_utils.is_in_jax_tracing_scope(sample_input)
        ):
            # We're in a TF graph, e.g. a tf.data pipeline.
            self.backend.set_backend("tensorflow")
            inputs = tree.map_structure(
                lambda x: self.backend.convert_to_tensor(
                    x, dtype=self.compute_dtype
                ),
                inputs,
            )
            switch_convert_input_args = False
            if self._convert_input_args:
                self._convert_input_args = False
                switch_convert_input_args = True
            try:
                outputs = super().__call__(inputs, **kwargs)
            finally:
                self.backend.reset()
                if switch_convert_input_args:
                    self._convert_input_args = True
            return outputs
        elif (
            not isinstance(sample_input, keras.KerasTensor)
            and backend_utils.in_grain_data_pipeline()
        ):
            # We're in a Grain data pipeline. Force computation and data
            # placement to CPU.
            with keras.src.backend.device_scope("cpu"):
                return super().__call__(inputs, **kwargs)
        else:
            return super().__call__(inputs, **kwargs)