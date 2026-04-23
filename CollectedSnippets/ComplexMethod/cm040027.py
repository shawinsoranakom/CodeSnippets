def __call__(self, data):
        self._check_if_built()
        if not isinstance(data, dict):
            raise ValueError(
                "A FeatureSpace can only be called with a dict. "
                f"Received: data={data} (of type {type(data)}"
            )

        # Many preprocessing layers support all backends but many do not.
        # Switch to TF to make FeatureSpace work universally.
        data = {key: self._convert_input(value) for key, value in data.items()}
        rebatched = False
        for name, x in data.items():
            if len(x.shape) == 0:
                data[name] = tf.reshape(x, (1, 1))
                rebatched = True
            elif len(x.shape) == 1:
                data[name] = tf.expand_dims(x, -1)

        with backend_utils.TFGraphScope():
            # This scope is to make sure that inner DataLayers
            # will not convert outputs back to backend-native --
            # they should be TF tensors throughout
            preprocessed_data = self._preprocess_features(data)
            preprocessed_data = tree.map_structure(
                lambda x: self._convert_input(x), preprocessed_data
            )

            crossed_data = self._cross_features(preprocessed_data)
            crossed_data = tree.map_structure(
                lambda x: self._convert_input(x), crossed_data
            )

            merged_data = self._merge_features(preprocessed_data, crossed_data)

        if rebatched:
            if self.output_mode == "concat":
                if merged_data.shape[0] != 1:
                    raise ValueError(
                        "Expected rebatched data to have batch size 1. "
                        f"Received: shape={merged_data.shape}"
                    )
                if (
                    backend.backend() != "tensorflow"
                    and not backend_utils.in_tf_graph()
                ):
                    merged_data = backend.convert_to_numpy(merged_data)
                merged_data = tf.squeeze(merged_data, axis=0)
            else:
                for name, x in merged_data.items():
                    if len(x.shape) == 2 and x.shape[0] == 1:
                        merged_data[name] = tf.squeeze(x, axis=0)

        if (
            backend.backend() != "tensorflow"
            and not backend_utils.in_tf_graph()
        ):
            merged_data = tree.map_structure(
                lambda x: backend.convert_to_tensor(x, dtype=x.dtype),
                merged_data,
            )
        return merged_data