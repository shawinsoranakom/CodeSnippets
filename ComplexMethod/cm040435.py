def sparse_wrapper(x1, x2):
        if isinstance(x1, tf.SparseTensor):
            if isinstance(x2, tf.SparseTensor):
                # x1 is a SparseTensor and x2 is a SparseTensor.
                if x1.indices is x2.indices:
                    return sparse_with_values(x1, func(x1.values, x2.values))
                else:
                    # Compute the intersection of indices.
                    (
                        intersection_indices,
                        x1_values_for_intersection,
                        x2_values_for_intersection,
                    ) = sparse_intersection_indices_and_values(x1, x2)
                    # Now, it is an element-wise operation on the intersection.
                    output = tf.SparseTensor(
                        intersection_indices,
                        func(
                            x1_values_for_intersection,
                            x2_values_for_intersection,
                        ),
                        x1.dense_shape,
                    )
                    output.set_shape(x1.shape)
                    return output
            else:
                # x1 is a SparseTensor.
                if not hasattr(x2, "shape") or len(x2.shape) == 0:
                    # x2 is a scalar, apply func element-wise.
                    return sparse_with_values(x1, func(x1.values, x2))
                else:
                    # x2 is dense, gather values from x1 indices.
                    return sparse_with_values(
                        x1, func(x1.values, tf.gather_nd(x2, x1.indices))
                    )
        elif isinstance(x2, tf.SparseTensor):
            # x2 is a SparseTensor.
            if not hasattr(x1, "shape") or len(x1.shape) == 0:
                # x1 is a scalar, apply func element-wise.
                return sparse_with_values(x2, func(x1, x2.values))
            else:
                # x1 is dense, gather values from x2 indices.
                return sparse_with_values(
                    x2, func(tf.gather_nd(x1, x2.indices), x2.values)
                )
        elif isinstance(x1, tf.IndexedSlices):
            if isinstance(x2, tf.IndexedSlices):
                # x1 is an IndexedSlices and x2 is an IndexedSlices.
                if x1.indices is x2.indices:
                    return tf.IndexedSlices(
                        func(x1.values, x2.values), x1.indices, x1.dense_shape
                    )
                else:
                    # Compute the intersection of indices.
                    (
                        intersection_indices,
                        x1_values_for_intersection,
                        x2_values_for_intersection,
                    ) = indexed_slices_intersection_indices_and_values(x1, x2)
                    # Now, it is an element-wise operation on the intersection.
                    return tf.IndexedSlices(
                        func(
                            x1_values_for_intersection,
                            x2_values_for_intersection,
                        ),
                        intersection_indices,
                        x1.dense_shape,
                    )
            else:
                # x1 is an IndexedSlices.
                if not hasattr(x2, "shape") or len(x2.shape) == 0:
                    # x2 is a scalar, apply func element-wise.
                    return tf.IndexedSlices(
                        func(x1.values, x2), x1.indices, x1.dense_shape
                    )
                else:
                    # x2 is dense, gather values from x1 indices.
                    return tf.IndexedSlices(
                        func(x1.values, tf.gather(x2, x1.indices)),
                        x1.indices,
                        x1.dense_shape,
                    )
        elif isinstance(x2, tf.IndexedSlices):
            # x2 is an IndexedSlices.
            if not hasattr(x1, "shape") or len(x1.shape) == 0:
                # x1 is a scalar, apply func element-wise.
                return tf.IndexedSlices(
                    func(x1, x2.values), x2.indices, x2.dense_shape
                )
            else:
                # x1 is dense, gather values from x2 indices.
                return tf.IndexedSlices(
                    func(tf.gather(x1, x2.indices), x2.values),
                    x2.indices,
                    x2.dense_shape,
                )
        # Default case, no SparseTensor and no IndexedSlices.
        return func(x1, x2)