def sparse_categorical_crossentropy(
    target, output, from_logits=False, axis=-1, ignore_class=None
):
    """DEPRECATED."""
    target = tf.convert_to_tensor(target)
    output = tf.convert_to_tensor(output)

    target = cast(target, "int64")

    if not from_logits:
        epsilon_ = tf.convert_to_tensor(backend.epsilon(), output.dtype)
        output = tf.clip_by_value(output, epsilon_, 1 - epsilon_)
        output = tf.math.log(output)

    # Permute output so that the last axis contains the logits/probabilities.
    if isinstance(output.shape, (tuple, list)):
        output_rank = len(output.shape)
    else:
        output_rank = output.shape.ndims
    if output_rank is not None:
        axis %= output_rank
        if axis != output_rank - 1:
            permutation = list(
                itertools.chain(
                    range(axis), range(axis + 1, output_rank), [axis]
                )
            )
            output = tf.transpose(output, perm=permutation)
    elif axis != -1:
        raise ValueError(
            "Cannot compute sparse categorical crossentropy with `axis={}` "
            "on an output tensor with unknown rank".format(axis)
        )

    # Try to adjust the shape so that rank of labels = rank of logits - 1.
    output_shape = tf.shape(output)
    target_rank = target.shape.ndims

    update_shape = (
        target_rank is not None
        and output_rank is not None
        and target_rank != output_rank - 1
    )
    if update_shape:
        target = flatten(target)
        output = tf.reshape(output, [-1, output_shape[-1]])

    if ignore_class is not None:
        valid_mask = tf.not_equal(target, cast(ignore_class, target.dtype))
        target = target[valid_mask]
        output = output[valid_mask]

    res = tf.nn.sparse_softmax_cross_entropy_with_logits(
        labels=target, logits=output
    )

    if ignore_class is not None:
        res_shape = cast(output_shape[:-1], "int64")
        valid_mask = tf.reshape(valid_mask, res_shape)
        res = tf.scatter_nd(tf.where(valid_mask), res, res_shape)
        res._keras_mask = valid_mask

        return res

    if update_shape and output_rank >= 3:
        # If our output includes timesteps or
        # spatial dimensions we need to reshape
        res = tf.reshape(res, output_shape[:-1])

    return res