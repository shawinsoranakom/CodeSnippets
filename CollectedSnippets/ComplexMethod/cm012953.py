def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a quantized sparse module from a float module.

        We only care about the convert at this stage, no need for observers just yet.

        TODO(zaf): Need to add the sparse params to the qconfig
        """
        if type(mod) is not cls._FLOAT_MODULE:
            raise AssertionError(
                cls._get_name()
                + ".from_float only works for "
                + cls._FLOAT_MODULE.__name__
            )
        if not hasattr(mod, "sparse_params"):
            raise AssertionError(
                "Expecting the Linear to have `sparse_params`. Make sure you have provided arguments "
                'in the `sparsifier.squash_mask(params_to_save=("sparse_block_shape",))` method.'
            )
        sparse_block_shape = mod.sparse_params.get("sparse_block_shape", None)  # type: ignore[operator, union-attr]
        if not isinstance(sparse_block_shape, (tuple, list)):
            raise AssertionError(
                f"sparse_block_shape must be tuple or list, got {type(sparse_block_shape)}"
            )
        if len(sparse_block_shape) != 2:
            raise AssertionError(
                f"sparse_block_shape must have length 2, got {len(sparse_block_shape)}"
            )
        # TODO: Need to add options to qconfig to avoid the calibration.
        # TODO: Add calibration for the sparsity
        if not hasattr(mod, "qconfig"):
            raise AssertionError("Input float module must have qconfig defined")
        activation_post_process = mod.activation_post_process
        weight_post_process = mod.qconfig.weight()  # type: ignore[operator, union-attr]

        # Assumption is that the weight is already sparsified by the
        # `sparsifier.convert`
        weight = mod.weight

        weight_post_process(weight)
        dtype = weight_post_process.dtype
        act_scale, act_zp = activation_post_process.calculate_qparams()  # type: ignore[operator, union-attr]
        if dtype != torch.qint8:
            raise AssertionError(
                f"Weight observer must have dtype torch.qint8, got {dtype}"
            )
        w_sc, w_zp = weight_post_process.calculate_qparams()
        if isinstance(w_zp, torch.Tensor):
            if torch.any(w_zp.bool()):
                raise AssertionError("All weight zero points must map to 0")
        else:
            if w_zp != 0:
                raise AssertionError(f"Weight zero point must map to 0, got {w_zp}")
        qweight = _quantize_weight(weight.float(), weight_post_process)

        row_block_size = mod.sparse_params["sparse_block_shape"][0]  # type: ignore[index]
        col_block_size = mod.sparse_params["sparse_block_shape"][1]  # type: ignore[index]
        qlinear = cls(
            mod.in_features,
            mod.out_features,
            row_block_size,
            col_block_size,
            dtype=dtype,
        )
        qlinear.set_weight_bias(
            qweight,
            mod.bias,
            row_block_size,  # type: ignore[arg-type]
            col_block_size,  # type: ignore[arg-type]
        )
        qlinear.scale = float(act_scale)
        qlinear.zero_point = int(act_zp)
        return qlinear