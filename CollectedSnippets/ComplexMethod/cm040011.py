def call(self, inputs):
        from keras.src.backend import tensorflow as tf_backend

        self._check_at_least_two_inputs(inputs)
        inputs = [tf_utils.ensure_tensor(x) for x in inputs]
        self._check_input_shape_and_type(inputs)

        with tf.device("CPU:0"):
            # Uprank to rank 2 for the cross_hashed op.
            first_shape = tuple(inputs[0].shape)
            rank = len(first_shape)
            if rank < 2:
                inputs = [tf_backend.numpy.expand_dims(x, -1) for x in inputs]
            if rank < 1:
                inputs = [tf_backend.numpy.expand_dims(x, -1) for x in inputs]

            # Perform the cross and convert to dense
            outputs = tf.sparse.cross_hashed(inputs, self.num_bins)
            outputs = tf.sparse.to_dense(outputs)

            # tf.sparse.cross_hashed output shape will always have None
            # dimensions. Re-apply the known static shape and downrank
            # to match input rank.
            if rank == 2:
                outputs.set_shape(first_shape)
            elif rank == 1:
                outputs.set_shape(first_shape + (1,))
                outputs = tf.squeeze(outputs, axis=1)
            elif rank == 0:
                outputs = tf.reshape(outputs, [])

            # Encode outputs.
            outputs = numerical_utils.encode_categorical_inputs(
                outputs,
                output_mode=self.output_mode,
                depth=self.num_bins,
                sparse=self.sparse,
                dtype=self.compute_dtype,
                backend_module=tf_backend,
            )
            return backend_utils.convert_tf_tensor(outputs, dtype=self.dtype)