def compute_iou(
    boxes1,
    boxes2,
    bounding_box_format,
    use_masking=False,
    mask_val=-1,
    image_shape=None,
):
    """Computes a lookup table vector containing the ious for a given set boxes.

    The lookup vector is to be indexed by [`boxes1_index`,`boxes2_index`] if
    boxes are unbatched and by [`batch`, `boxes1_index`,`boxes2_index`] if the
    boxes are batched.

    The users can pass `boxes1` and `boxes2` to be different ranks. For example:
    1) `boxes1`: [batch_size, M, 4], `boxes2`: [batch_size, N, 4] -> return
        [batch_size, M, N].
    2) `boxes1`: [batch_size, M, 4], `boxes2`: [N, 4] -> return
        [batch_size, M, N]
    3) `boxes1`: [M, 4], `boxes2`: [batch_size, N, 4] -> return
        [batch_size, M, N]
    4) `boxes1`: [M, 4], `boxes2`: [N, 4] -> return [M, N]

    Args:
        boxes1: a list of bounding boxes in 'corners' format. Can be batched or
            unbatched.
        boxes2: a list of bounding boxes in 'corners' format. Can be batched or
            unbatched.
        bounding_box_format: a case-insensitive string which is one of `"xyxy"`,
            `"rel_xyxy"`, `"xyWH"`, `"center_xyWH"`, `"yxyx"`, `"rel_yxyx"`.
            For detailed information on the supported format, see the
        use_masking: whether masking will be applied. This will mask all
            `boxes1` or `boxes2` that have values less than 0 in all its 4
            dimensions. Default to `False`.
        mask_val: int to mask those returned IOUs if the masking is True,
            defaults to -1.
        image_shape: `Tuple[int]`. The shape of the image (height, width, 3).
            When using relative bounding box format for `box_format` the
            `image_shape` is used for normalization.

    Returns:
        iou_lookup_table: a vector containing the pairwise ious of boxes1 and
            boxes2.
    """  # noqa: E501

    boxes1_rank = len(ops.shape(boxes1))
    boxes2_rank = len(ops.shape(boxes2))

    if boxes1_rank not in [2, 3]:
        raise ValueError(
            "compute_iou() expects boxes1 to be batched, or to be unbatched. "
            f"Received len(boxes1.shape)={boxes1_rank}, "
            f"len(boxes2.shape)={boxes2_rank}. Expected either "
            "len(boxes1.shape)=2 AND or len(boxes1.shape)=3."
        )
    if boxes2_rank not in [2, 3]:
        raise ValueError(
            "compute_iou() expects boxes2 to be batched, or to be unbatched. "
            f"Received len(boxes1.shape)={boxes1_rank}, "
            f"len(boxes2.shape)={boxes2_rank}. Expected either "
            "len(boxes2.shape)=2 AND or len(boxes2.shape)=3."
        )

    target_format = "yxyx"
    if "rel" in bounding_box_format and image_shape is None:
        raise ValueError(
            "When using relative bounding box formats (e.g. `rel_yxyx`) "
            "the `image_shape` argument must be provided."
            f"Received `image_shape`: {image_shape}"
        )

    if image_shape is None:
        height, width = None, None
    else:
        height, width, _ = image_shape

    boxes1 = converters.convert_format(
        boxes1,
        source=bounding_box_format,
        target=target_format,
        height=height,
        width=width,
    )

    boxes2 = converters.convert_format(
        boxes2,
        source=bounding_box_format,
        target=target_format,
        height=height,
        width=width,
    )

    intersect_area = _compute_intersection(boxes1, boxes2)
    boxes1_area = _compute_area(boxes1)
    boxes2_area = _compute_area(boxes2)
    boxes2_area_rank = len(boxes2_area.shape)
    boxes2_axis = 1 if (boxes2_area_rank == 2) else 0
    boxes1_area = ops.expand_dims(boxes1_area, axis=-1)
    boxes2_area = ops.expand_dims(boxes2_area, axis=boxes2_axis)
    union_area = boxes1_area + boxes2_area - intersect_area
    res = ops.divide(intersect_area, union_area + backend.epsilon())

    if boxes1_rank == 2:
        perm = [1, 0]
    else:
        perm = [0, 2, 1]

    if not use_masking:
        return res

    mask_val_t = ops.cast(mask_val, res.dtype) * ops.ones_like(res)
    boxes1_mask = ops.less(ops.max(boxes1, axis=-1, keepdims=True), 0.0)
    boxes2_mask = ops.less(ops.max(boxes2, axis=-1, keepdims=True), 0.0)
    background_mask = ops.logical_or(
        boxes1_mask, ops.transpose(boxes2_mask, perm)
    )
    iou_lookup_table = ops.where(background_mask, mask_val_t, res)
    return iou_lookup_table