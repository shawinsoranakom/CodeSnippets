def resize(
    images,
    size,
    interpolation="bilinear",
    antialias=False,
    crop_to_aspect_ratio=False,
    pad_to_aspect_ratio=False,
    fill_mode="constant",
    fill_value=0.0,
    data_format="channels_last",
):
    data_format = backend.standardize_data_format(data_format)
    if interpolation in UNSUPPORTED_INTERPOLATIONS:
        raise ValueError(
            "Resizing with Lanczos interpolation is "
            "not supported by the OpenVINO backend. "
            f"Received: interpolation={interpolation}."
        )
    if interpolation not in RESIZE_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{tuple(RESIZE_INTERPOLATIONS.keys())}. Received: "
            f"interpolation={interpolation}"
        )
    if fill_mode != "constant":
        raise ValueError(
            "Invalid value for argument `fill_mode`. Only `'constant'` "
            f"is supported. Received: fill_mode={fill_mode}"
        )
    if pad_to_aspect_ratio and crop_to_aspect_ratio:
        raise ValueError(
            "Only one of `pad_to_aspect_ratio` & `crop_to_aspect_ratio` "
            "can be `True`."
        )
    if not len(size) == 2:
        raise ValueError(
            "Argument `size` must be a tuple of two elements "
            f"(height, width). Received: size={size}"
        )

    target_height, target_width = tuple(size)
    images = get_ov_output(images)
    rank = len(images.get_partial_shape())
    if rank not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.get_partial_shape()}"
        )

    if data_format == "channels_last":
        height_axis, width_axis = (-3, -2)
    else:
        height_axis, width_axis = (-2, -1)

    def _gather_dim(shape_tensor, axis):
        axis_node = ov_opset.constant([axis], Type.i32).output(0)
        axis0 = ov_opset.constant(0, Type.i32).output(0)
        return ov_opset.gather(shape_tensor, axis_node, axis0).output(0)

    def _floor_div_int(numerator, denominator):
        numerator_f = ov_opset.convert(numerator, Type.f32).output(0)
        denominator_f = ov_opset.convert(denominator, Type.f32).output(0)
        quotient = ov_opset.divide(numerator_f, denominator_f).output(0)
        floored = ov_opset.floor(quotient).output(0)
        return ov_opset.convert(floored, Type.i32).output(0)

    def _concat_scalars(nodes):
        return ov_opset.concat(nodes, axis=0).output(0)

    shape_node = ov_opset.shape_of(images, Type.i32).output(0)
    height_axis_index = height_axis % rank
    width_axis_index = width_axis % rank
    height = _gather_dim(shape_node, height_axis_index)
    width = _gather_dim(shape_node, width_axis_index)

    target_height_node = ov_opset.constant([target_height], Type.i32).output(0)
    target_width_node = ov_opset.constant([target_width], Type.i32).output(0)
    one_i32 = ov_opset.constant([1], Type.i32).output(0)
    zero_i32 = ov_opset.constant([0], Type.i32).output(0)

    if crop_to_aspect_ratio:
        crop_height = _floor_div_int(
            ov_opset.multiply(width, target_height_node).output(0),
            target_width_node,
        )
        crop_height = ov_opset.minimum(height, crop_height).output(0)
        crop_height = ov_opset.maximum(one_i32, crop_height).output(0)

        crop_width = _floor_div_int(
            ov_opset.multiply(height, target_width_node).output(0),
            target_height_node,
        )
        crop_width = ov_opset.minimum(width, crop_width).output(0)
        crop_width = ov_opset.maximum(one_i32, crop_width).output(0)

        crop_box_hstart = _floor_div_int(
            ov_opset.subtract(height, crop_height).output(0),
            ov_opset.constant([2], Type.i32).output(0),
        )
        crop_box_wstart = _floor_div_int(
            ov_opset.subtract(width, crop_width).output(0),
            ov_opset.constant([2], Type.i32).output(0),
        )

        crop_box_hend = ov_opset.add(crop_box_hstart, crop_height).output(0)
        crop_box_wend = ov_opset.add(crop_box_wstart, crop_width).output(0)

        begin_parts = []
        end_parts = []
        begin_mask = [1] * rank
        end_mask = [1] * rank
        for axis in range(rank):
            if axis == height_axis_index:
                begin_parts.append(crop_box_hstart)
                end_parts.append(crop_box_hend)
                begin_mask[axis] = 0
                end_mask[axis] = 0
            elif axis == width_axis_index:
                begin_parts.append(crop_box_wstart)
                end_parts.append(crop_box_wend)
                begin_mask[axis] = 0
                end_mask[axis] = 0
            else:
                begin_parts.append(zero_i32)
                end_parts.append(zero_i32)

        images = ov_opset.strided_slice(
            data=images,
            begin=_concat_scalars(begin_parts),
            end=_concat_scalars(end_parts),
            strides=ov_opset.constant([1] * rank, Type.i32).output(0),
            begin_mask=begin_mask,
            end_mask=end_mask,
        ).output(0)
    elif pad_to_aspect_ratio:
        pad_height = _floor_div_int(
            ov_opset.multiply(width, target_height_node).output(0),
            target_width_node,
        )
        pad_height = ov_opset.maximum(height, pad_height).output(0)

        pad_width = _floor_div_int(
            ov_opset.multiply(height, target_width_node).output(0),
            target_height_node,
        )
        pad_width = ov_opset.maximum(width, pad_width).output(0)

        img_box_hstart = _floor_div_int(
            ov_opset.subtract(pad_height, height).output(0),
            ov_opset.constant([2], Type.i32).output(0),
        )
        img_box_wstart = _floor_div_int(
            ov_opset.subtract(pad_width, width).output(0),
            ov_opset.constant([2], Type.i32).output(0),
        )

        pads_begin_parts = []
        pads_end_parts = []
        for axis in range(rank):
            if axis == height_axis_index:
                pads_begin_parts.append(img_box_hstart)
                pads_end_parts.append(img_box_hstart)
            elif axis == width_axis_index:
                pads_begin_parts.append(img_box_wstart)
                pads_end_parts.append(img_box_wstart)
            else:
                pads_begin_parts.append(zero_i32)
                pads_end_parts.append(zero_i32)

        fill_value = ov_opset.constant(
            fill_value, images.get_element_type()
        ).output(0)
        images = ov_opset.pad(
            images,
            _concat_scalars(pads_begin_parts),
            _concat_scalars(pads_end_parts),
            "constant",
            fill_value,
        ).output(0)

    axes = [height_axis % rank, width_axis % rank]
    size = ov_opset.constant([target_height, target_width], Type.i32).output(0)
    axes = ov_opset.constant(axes, Type.i32).output(0)

    original_type = images.get_element_type()
    supported_types = {
        Type.f32,
        Type.f16,
        Type.bf16,
        Type.i8,
        Type.u8,
        Type.i32,
        Type.i64,
    }
    should_round_before_cast = False
    should_adjust_uint8_bicubic = False
    if original_type == Type.u8 and interpolation != "nearest":
        images = ov_opset.convert(images, Type.f32).output(0)
        should_round_before_cast = True
        if interpolation == "bicubic":
            should_adjust_uint8_bicubic = True
    elif original_type not in supported_types:
        images = ov_opset.convert(images, Type.f32).output(0)

    interpolate_kwargs = {
        "mode": RESIZE_INTERPOLATIONS[interpolation],
        "shape_calculation_mode": "sizes",
        "antialias": antialias,
        "axes": axes,
    }
    if interpolation == "nearest":
        interpolate_kwargs["coordinate_transformation_mode"] = (
            "tf_half_pixel_for_nn"
        )
        interpolate_kwargs["nearest_mode"] = "simple"
    elif interpolation == "bicubic":
        interpolate_kwargs["coordinate_transformation_mode"] = "half_pixel"
        interpolate_kwargs["cube_coeff"] = -0.5
    else:
        interpolate_kwargs["coordinate_transformation_mode"] = "half_pixel"

    resized = ov_opset.interpolate(images, size, **interpolate_kwargs).output(0)

    if should_round_before_cast:
        resized = ov_opset.round(resized, "half_to_even").output(0)
        if should_adjust_uint8_bicubic:
            # Match TensorFlow/OpenCV-style uint8 bicubic behavior more closely
            # by nudging non-extreme values toward mid-range before clamping.
            low_mask = ov_opset.logical_and(
                ov_opset.greater(resized, ov_opset.constant(0.0, Type.f32)),
                ov_opset.less(resized, ov_opset.constant(128.0, Type.f32)),
            ).output(0)
            high_mask = ov_opset.logical_and(
                ov_opset.greater_equal(
                    resized, ov_opset.constant(128.0, Type.f32)
                ),
                ov_opset.less(resized, ov_opset.constant(255.0, Type.f32)),
            ).output(0)
            plus_one = ov_opset.add(
                resized,
                ov_opset.convert(low_mask, Type.f32),
            ).output(0)
            resized = ov_opset.subtract(
                plus_one,
                ov_opset.convert(high_mask, Type.f32),
            ).output(0)
        resized = ov_opset.clamp(resized, 0.0, 255.0).output(0)
    if resized.get_element_type() != original_type:
        resized = ov_opset.convert(resized, original_type).output(0)
    return OpenVINOKerasTensor(resized)