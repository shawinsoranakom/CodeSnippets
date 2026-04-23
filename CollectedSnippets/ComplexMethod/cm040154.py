def reduce_values(values, sample_weight=None, reduction="sum_over_batch_size"):
    if (
        reduction is None
        or reduction == "none"
        or tuple(values.shape) == ()
        or tuple(values.shape) == (0,)
    ):
        return values
    loss = ops.sum(values)
    if reduction in ("sum_over_batch_size", "mean", "mean_with_sample_weight"):
        if reduction == "mean_with_sample_weight" and sample_weight is not None:
            divisor = ops.cast(ops.sum(sample_weight), loss.dtype)
        else:
            divisor = ops.cast(
                ops.prod(
                    ops.convert_to_tensor(ops.shape(values), dtype="int32")
                ),
                loss.dtype,
            )
        loss = ops.divide_no_nan(loss, divisor)
        loss = scale_loss_for_distribution(loss)
    return loss