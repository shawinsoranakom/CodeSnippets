def decode_deltas_to_boxes(
    anchors,
    boxes_delta,
    anchor_format,
    box_format,
    encoded_format="center_yxhw",
    variance=None,
    image_shape=None,
):
    """Converts bounding boxes from delta format to the specified `box_format`.

    This function decodes bounding box deltas relative to anchors to obtain the
    final bounding box coordinates. The boxes are encoded in a specific
    `encoded_format` (center_yxhw by default) during the decoding process.
    This allows flexibility in how the deltas are applied to the anchors.

    Args:
        anchors: Can be `Tensors` or `Dict[Tensors]` where keys are level
            indices and values are corresponding anchor boxes.
            The shape of the array/tensor should be `(N, 4)` where N is the
            number of anchors.
        boxes_delta Can be `Tensors` or `Dict[Tensors]` Bounding box deltas
            must have the same type and structure as `anchors`.  The
            shape of the array/tensor can be `(N, 4)` or `(B, N, 4)` where N is
            the number of boxes.
        anchor_format: str. The format of the input `anchors`.
            (e.g., `"xyxy"`, `"xywh"`, etc.)
        box_format: str. The desired format for the output boxes.
            (e.g., `"xyxy"`, `"xywh"`, etc.)
        encoded_format: str. Raw output format from regression head. Defaults
            to `"center_yxhw"`.
        variance: `List[floats]`. A 4-element array/tensor representing
            variance factors to scale the box deltas. If provided, the deltas
            are multiplied by the variance before being applied to the anchors.
            Defaults to None.
        image_shape: `Tuple[int]`. The shape of the image (height, width, 3).
            When using relative bounding box format for `box_format` the
            `image_shape` is used for normalization.

    Returns:
        Decoded box coordinates. The return type matches the `box_format`.

    Raises:
        ValueError: If `variance` is not None and its length is not 4.
        ValueError: If `encoded_format` is not `"center_xywh"` or
            `"center_yxhw"`.

    """
    if variance is not None:
        variance = ops.convert_to_tensor(variance, "float32")
        var_len = variance.shape[-1]

        if var_len != 4:
            raise ValueError(f"`variance` must be length 4, got {variance}")

    if encoded_format not in ["center_xywh", "center_yxhw"]:
        raise ValueError(
            f"`encoded_format` should be 'center_xywh' or 'center_yxhw', "
            f"but got '{encoded_format}'."
        )

    if image_shape is None:
        height, width = None, None
    else:
        height, width, _ = image_shape

    def decode_single_level(anchor, box_delta):
        encoded_anchor = convert_format(
            anchor,
            source=anchor_format,
            target=encoded_format,
            height=height,
            width=width,
        )
        if variance is not None:
            box_delta = box_delta * variance
        # anchors be unbatched, boxes can either be batched or unbatched.
        box = ops.concatenate(
            [
                box_delta[..., :2] * encoded_anchor[..., 2:]
                + encoded_anchor[..., :2],
                ops.exp(box_delta[..., 2:]) * encoded_anchor[..., 2:],
            ],
            axis=-1,
        )
        box = convert_format(
            box,
            source=encoded_format,
            target=box_format,
            height=height,
            width=width,
        )
        return box

    if isinstance(anchors, dict) and isinstance(boxes_delta, dict):
        boxes = {}
        for lvl, anchor in anchors.items():
            boxes[lvl] = decode_single_level(anchor, boxes_delta[lvl])
        return boxes
    else:
        return decode_single_level(anchors, boxes_delta)