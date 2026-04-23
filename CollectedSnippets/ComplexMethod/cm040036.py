def call(self, inputs):
        from keras.src.backend import tensorflow as tf_backend

        self._ensure_known_vocab_size()
        with tf.device("CPU:0"):
            inputs = tf_utils.ensure_tensor(inputs, dtype=self._key_dtype)
            original_shape = inputs.shape
            # Some ops will not handle scalar input, so uprank to rank 1.
            if inputs.shape.rank == 0:
                inputs = self._expand_dims(inputs, -1)

            if isinstance(inputs, tf.SparseTensor):
                lookups = tf.SparseTensor(
                    inputs.indices,
                    self._lookup_dense(inputs.values),
                    inputs.dense_shape,
                )
            elif isinstance(inputs, tf.RaggedTensor):
                lookups = tf.ragged.map_flat_values(self._lookup_dense, inputs)
            else:
                lookups = self._lookup_dense(inputs)

            if self.output_mode == "int":
                # If we received a scalar input, downrank back to a scalar.
                if original_shape.rank == 0:
                    lookups = tf.squeeze(lookups, -1)
                return lookups

            depth = (
                self.max_tokens
                if self.pad_to_max_tokens
                else self._frozen_vocab_size
            )
            idf_weights = (
                self.idf_weights_const if self.output_mode == "tf_idf" else None
            )
            output = numerical_utils.encode_categorical_inputs(
                lookups,
                output_mode=(
                    "count"
                    if self.output_mode == "tf_idf"
                    else self.output_mode
                ),
                depth=depth,
                dtype=self._value_dtype,
                sparse=self.sparse,
                backend_module=tf_backend,
            )
            if self.output_mode == "tf_idf":
                if idf_weights is None:
                    raise ValueError(
                        "When `output_mode` is `'tf_idf'`, "
                        "`idf_weights` must be provided."
                    )
                output = tf_backend.numpy.multiply(
                    tf_backend.core.cast(output, idf_weights.dtype), idf_weights
                )
            return output