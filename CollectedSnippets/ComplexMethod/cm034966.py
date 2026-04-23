def create_resnetv2_stem(
    in_chs,
    out_chs=64,
    stem_type="",
    preact=True,
    conv_layer=StdConv2d,
    norm_layer=partial(GroupNormAct, num_groups=32),
    is_export=False,
):
    stem = OrderedDict()
    assert stem_type in (
        "",
        "fixed",
        "same",
        "deep",
        "deep_fixed",
        "deep_same",
        "tiered",
    )

    # NOTE conv padding mode can be changed by overriding the conv_layer def
    if is_stem_deep(stem_type):
        # A 3 deep 3x3  conv stack as in ResNet V1D models
        if "tiered" in stem_type:
            stem_chs = (3 * out_chs // 8, out_chs // 2)  # 'T' resnets in resnet.py
        else:
            stem_chs = (out_chs // 2, out_chs // 2)  # 'D' ResNets
        stem["conv1"] = conv_layer(
            in_chs, stem_chs[0], kernel_size=3, stride=2, is_export=is_export
        )
        stem["norm1"] = norm_layer(stem_chs[0])
        stem["conv2"] = conv_layer(
            stem_chs[0], stem_chs[1], kernel_size=3, stride=1, is_export=is_export
        )
        stem["norm2"] = norm_layer(stem_chs[1])
        stem["conv3"] = conv_layer(
            stem_chs[1], out_chs, kernel_size=3, stride=1, is_export=is_export
        )
        if not preact:
            stem["norm3"] = norm_layer(out_chs)
    else:
        # The usual 7x7 stem conv
        stem["conv"] = conv_layer(
            in_chs, out_chs, kernel_size=7, stride=2, is_export=is_export
        )
        if not preact:
            stem["norm"] = norm_layer(out_chs)

    if "fixed" in stem_type:
        # 'fixed' SAME padding approximation that is used in BiT models
        stem["pad"] = paddle.nn.Pad2D(
            1, mode="constant", value=0.0, data_format="NCHW", name=None
        )
        stem["pool"] = nn.MaxPool2D(kernel_size=3, stride=2, padding=0)
    elif "same" in stem_type:
        # full, input size based 'SAME' padding, used in ViT Hybrid model
        stem["pool"] = create_pool2d(
            "max", kernel_size=3, stride=2, padding="same", is_export=is_export
        )
    else:
        # the usual Pypaddle symmetric padding
        stem["pool"] = nn.MaxPool2D(kernel_size=3, stride=2, padding=1)
    stem_seq = nn.Sequential()
    for key, value in stem.items():
        stem_seq.add_sublayer(key, value)

    return stem_seq