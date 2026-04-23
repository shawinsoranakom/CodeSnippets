def sparse_wrapper(x1, x2):
        if isinstance(x1, tf.SparseTensor):
            if isinstance(x2, tf.SparseTensor):
                # x1 is a SparseTensor and x2 is a SparseTensor.
                # Divisor is sparse, meaning we're doing divisions by zero
                # outside of x2.indices, so the result is dense. Densify both.
                x1 = sparse_to_dense(x1)
                x2 = sparse_to_dense(x2)
            else:
                # x1 is a SparseTensor.
                if not hasattr(x2, "shape") or len(x2.shape) == 0:
                    # x2 is a scalar, apply func element-wise.
                    return sparse_with_values(x1, func(x1.values, x2))
                else:
                    # x2 is dense.
                    x2_zeros_and_nans = tf.equal(x2, 0)
                    if not tf.as_dtype(x2.dtype).is_integer:
                        x2_zeros_and_nans = tf.math.logical_or(
                            x2_zeros_and_nans, tf.math.is_nan(x2)
                        )

                    def func_for_x1_indices():
                        # Gather values from x1 indices.
                        return sparse_with_values(
                            x1, func(x1.values, tf.gather_nd(x2, x1.indices))
                        )

                    def func_for_union_indices():
                        # Compute the union of indices to keep zeros and NaNs.
                        x2_zeros_and_nan_indices = tf.where(x2_zeros_and_nans)
                        (
                            union_indices,
                            x1_values_for_union,
                            _,
                        ) = sparse_union_indices_and_values(
                            x1, x2_zeros_and_nan_indices
                        )
                        output = tf.SparseTensor(
                            union_indices,
                            func(
                                x1_values_for_union,
                                tf.gather_nd(x2, union_indices),
                            ),
                            x1.dense_shape,
                        )
                        output.set_shape(x1.shape)
                        return output

                    return tf.cond(
                        tf.reduce_any(x2_zeros_and_nans),
                        func_for_union_indices,
                        func_for_x1_indices,
                    )
        elif isinstance(x2, tf.SparseTensor):
            # x2 is a SparseTensor.
            # Divisor is sparse, densify to do the divisions by zero correctly.
            x2 = sparse_to_dense(x2)
        elif isinstance(x1, tf.IndexedSlices):
            if isinstance(x2, tf.IndexedSlices):
                # x1 is an IndexedSlices and x2 is an IndexedSlices.
                # Divisor is slices, meaning we're doing divisions by zero
                # outside of x2.indices, so the result is dense. Densify both.
                x1 = tf.convert_to_tensor(x1)
                x2 = tf.convert_to_tensor(x2)
            else:
                # x1 is a IndexedSlices.
                if not hasattr(x2, "shape") or len(x2.shape) == 0:
                    # x2 is a scalar, apply func element-wise.
                    return tf.IndexedSlices(
                        func(x1.values, x2), x1.indices, x1.dense_shape
                    )
                else:
                    # x2 is dense.
                    x2_zeros_and_nans = tf.equal(x2, 0)
                    if not tf.as_dtype(x2.dtype).is_integer:
                        x2_zeros_and_nans = tf.math.logical_or(
                            x2_zeros_and_nans, tf.math.is_nan(x2)
                        )
                    x2_zeros_and_nans = tf.reduce_any(
                        x2_zeros_and_nans, axis=tuple(range(1, x2.shape.rank))
                    )

                    def func_for_x1_indices():
                        # Gather values from x1 indices.
                        return tf.IndexedSlices(
                            func(x1.values, tf.gather(x2, x1.indices)),
                            x1.indices,
                            x1.dense_shape,
                        )

                    def func_for_union_indices():
                        x2_zeros_and_nan_indices = tf.squeeze(
                            tf.where(x2_zeros_and_nans), axis=-1
                        )
                        # Compute the union of indices to keep zeros and NaNs.
                        (
                            union_indices,
                            x1_values_for_union,
                            _,
                        ) = indexed_slices_union_indices_and_values(
                            x1, x2_zeros_and_nan_indices
                        )
                        return tf.IndexedSlices(
                            func(
                                x1_values_for_union,
                                tf.gather(x2, union_indices),
                            ),
                            union_indices,
                            x1.dense_shape,
                        )

                    return tf.cond(
                        tf.reduce_any(x2_zeros_and_nans),
                        func_for_union_indices,
                        func_for_x1_indices,
                    )
        elif isinstance(x2, tf.IndexedSlices):
            # x2 is a IndexedSlices.
            # Divisor is slices, densify to do the divisions by zero correctly.
            x2 = tf.convert_to_tensor(x2)
        # Default case, no SparseTensor and no IndexedSlices.
        return func(x1, x2)