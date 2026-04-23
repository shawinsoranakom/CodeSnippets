def fuse_conv_bn_relu(is_qat, conv, bn, relu):
    r"""Return the fused conv and bv modules.

    Given the conv and bn modules, fuses them and returns the fused module

    Args:
        is_qat: a flag for whether we are using quantization aware training fusion
        or post training quantization fusion
        conv: Module instance of type conv2d/conv3d
        bn: Spatial BN instance that needs to be fused with the conv

    Examples::

        >>> m1 = nn.Conv2d(10, 20, 3)
        >>> b1 = nn.BatchNorm2d(20)
        >>> r1 = nn.ReLU(inplace=False)
        >>> # xdoctest: +SKIP
        >>> m2 = fuse_conv_bn_relu(m1, b1, r1)
    """
    if not (conv.training == bn.training == relu.training):
        raise AssertionError(
            "Conv and BN both must be in the same mode (train or eval)."
        )
    fused_module: type[nn.Sequential] | None = None
    if is_qat:
        map_to_fused_module_train = {
            nn.Conv1d: nni.ConvBnReLU1d,
            nn.Conv2d: nni.ConvBnReLU2d,
            nn.Conv3d: nni.ConvBnReLU3d,
        }
        if bn.num_features != conv.out_channels:
            raise AssertionError(
                "Output channel of Conv2d must match num_features of BatchNorm2d"
            )
        if not bn.affine:
            raise AssertionError(
                "Only support fusing BatchNorm2d with affine set to True"
            )
        if not bn.track_running_stats:
            raise AssertionError(
                "Only support fusing BatchNorm2d with tracking_running_stats set to True"
            )
        fused_module = map_to_fused_module_train.get(type(conv))
        if fused_module is not None:
            return fused_module(conv, bn, relu)
        else:
            raise NotImplementedError(f"Cannot fuse train modules: {(conv, bn, relu)}")
    else:
        map_to_fused_module_eval = {
            nn.Conv1d: nni.ConvReLU1d,
            nn.Conv2d: nni.ConvReLU2d,
            nn.Conv3d: nni.ConvReLU3d,
        }
        fused_module = map_to_fused_module_eval.get(type(conv))
        if fused_module is not None:
            fused_conv = nn.utils.fusion.fuse_conv_bn_eval(conv, bn)
            return fused_module(fused_conv, relu)
        else:
            raise NotImplementedError(f"Cannot fuse eval modules: {(conv, bn, relu)}")