def affine_transform(
    images,
    transform,
    interpolation="bilinear",
    fill_mode="constant",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{set(AFFINE_TRANSFORM_INTERPOLATIONS.keys())}. Received: "
            f"interpolation={interpolation}"
        )
    if fill_mode not in AFFINE_TRANSFORM_FILL_MODES:
        raise ValueError(
            "Invalid value for argument `fill_mode`. Expected of one "
            f"{AFFINE_TRANSFORM_FILL_MODES}. Received: fill_mode={fill_mode}"
        )

    images = convert_to_tensor(images)
    transform = convert_to_tensor(transform)
    images_ov = get_ov_output(images)
    transform_ov = get_ov_output(transform)

    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    if len(transform.shape) not in (1, 2):
        raise ValueError(
            "Invalid transform rank: expected rank 1 (single transform) "
            "or rank 2 (batch of transforms). Received input with shape: "
            f"transform.shape={transform.shape}"
        )

    ov_type = images_ov.get_element_type()
    compute_type = Type.f32

    need_squeeze = False
    if len(images.shape) == 3:
        images_ov = ov_opset.unsqueeze(images_ov, axes=[0]).output(0)
        need_squeeze = True
    if len(transform.shape) == 1:
        transform_ov = ov_opset.unsqueeze(transform_ov, axes=[0]).output(0)

    if data_format == "channels_first":
        images_ov = ov_opset.transpose(
            images_ov,
            ov_opset.constant([0, 2, 3, 1], Type.i32).output(0),
        ).output(0)

    images_ov = ov_opset.convert(images_ov, compute_type).output(0)
    transform_ov = ov_opset.convert(transform_ov, compute_type).output(0)

    coords = _ov_build_affine_coords(images_ov, transform_ov)
    affined = map_coordinates(
        OpenVINOKerasTensor(images_ov),
        OpenVINOKerasTensor(coords),
        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
        fill_mode=fill_mode,
        fill_value=fill_value,
    )
    affined = get_ov_output(affined)

    if ov_type.is_integral():
        affined = ov_opset.round(affined, mode="half_to_even").output(0)
    affined = ov_opset.convert(affined, ov_type).output(0)

    if data_format == "channels_first":
        affined = ov_opset.transpose(
            affined,
            ov_opset.constant([0, 3, 1, 2], Type.i32).output(0),
        ).output(0)
    if need_squeeze:
        affined = ov_opset.squeeze(affined, axes=[0]).output(0)

    return OpenVINOKerasTensor(affined)