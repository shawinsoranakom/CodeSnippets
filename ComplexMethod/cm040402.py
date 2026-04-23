def concatenate(xs, axis=0):
    sparse_count = builtins.sum(isinstance(x, tf.SparseTensor) for x in xs)
    if sparse_count:
        if sparse_count == len(xs):
            return tf.sparse.concat(axis=axis, sp_inputs=xs)
        else:
            xs = [
                (
                    convert_to_tensor(x, sparse=False)
                    if isinstance(x, tf.SparseTensor)
                    else x
                )
                for x in xs
            ]
    xs = tree.map_structure(convert_to_tensor, xs)
    dtype_set = set([x.dtype for x in xs])
    if len(dtype_set) > 1:
        dtype = dtypes.result_type(*dtype_set)
        xs = tree.map_structure(lambda x: tf.cast(x, dtype), xs)
    return tf.concat(xs, axis=axis)