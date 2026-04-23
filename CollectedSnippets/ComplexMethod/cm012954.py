def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a quantized sparse dynamic module from a float module.

        We only care about the convert at this stage, no need for observers just yet.
        """
        if type(mod) is not cls._FLOAT_MODULE:
            raise AssertionError(
                " nnq."
                + cls.__name__
                + ".from_float only works for "
                + cls._FLOAT_MODULE.__name__
            )
        # TODO: Need to add options to qconfig to avoid the calibration.
        # TODO: Add calibration for the sparsity
        if not hasattr(mod, "qconfig"):
            raise AssertionError("Input float module must have qconfig defined")
        if type(mod) is nni.LinearReLU:
            mod = mod[0]
        # pyrefly: ignore [missing-attribute]
        if mod.qconfig is not None and mod.qconfig.weight is not None:
            # pyrefly: ignore [not-callable]
            weight_observer = mod.qconfig.weight()
        else:
            # We have the circular import issues if we import the qconfig in the beginning of this file:
            # https://github.com/pytorch/pytorch/pull/24231. The current workaround is to postpone the
            # import until we need it.
            from torch.ao.quantization.qconfig import default_dynamic_qconfig

            weight_observer = default_dynamic_qconfig.weight()

        # It is important to multiply by the mask BEFORE calling the `weight_observer`
        # TODO (zaf): Mask might not be part of the qconfig (T83295194)
        weight = mod.weight
        if getattr(mod.qconfig, "mask", False):
            weight = mod.qconfig.mask * mod.weight

        weight_observer(weight)
        dtype = weight_observer.dtype
        if dtype != torch.qint8:
            raise AssertionError(
                f"Weight observer must have dtype torch.qint8, got {dtype}"
            )
        _w_sc, w_zp = weight_observer.calculate_qparams()
        if isinstance(w_zp, torch.Tensor):
            if torch.any(w_zp.bool()):
                raise AssertionError("All weight zero points must map to 0")
        else:
            if w_zp != 0:
                raise AssertionError(f"Weight zero point must map to 0, got {w_zp}")
        qweight = _quantize_weight(weight.float(), weight_observer)

        row_block_size, col_block_size = LinearBlockSparsePattern.block_size()
        qlinear = cls(
            mod.in_features,
            mod.out_features,
            row_block_size,
            col_block_size,
            dtype=dtype,
        )
        # pyrefly: ignore [bad-argument-type]
        qlinear.set_weight_bias(qweight, mod.bias, row_block_size, col_block_size)
        return qlinear