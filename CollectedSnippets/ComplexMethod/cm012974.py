def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a quantized module from an observed float module

        Args:
            mod (Module): a float module, either produced by torch.ao.quantization
                          utilities or provided by the user
            use_precomputed_fake_quant (bool): if True, the module will reuse min/max
                          values from the precomputed fake quant module.
        """
        if hasattr(mod, "weight_fake_quant"):
            if type_before_parametrizations(mod) == nniqat.LinearBn1d:
                mod.weight, mod.bias = fuse_linear_bn_weights(
                    mod.weight,
                    mod.bias,
                    mod.bn.running_mean,
                    mod.bn.running_var,
                    mod.bn.eps,
                    mod.bn.weight,
                    mod.bn.bias,
                )
            weight_post_process = mod.weight_fake_quant
            activation_post_process = mod.activation_post_process
        else:
            # This function does not participate in JIT, so it is OK to ignore
            # the type mismatch in assignment. Also, mypy has an issue with
            # iterables not being implemented, so we are ignoring those too.
            if not isinstance(cls._FLOAT_MODULE, Iterable):
                # pyrefly: ignore [bad-assignment]
                cls._FLOAT_MODULE = [cls._FLOAT_MODULE]
            supported_modules = ", ".join(
                [float_mod.__name__ for float_mod in cls._FLOAT_MODULE]
            )
            error_msg = f"nnq.{cls.__name__}.from_float only works for {supported_modules}, but got: {type(mod)}"
            if type_before_parametrizations(mod) not in cls._FLOAT_MODULE:
                raise AssertionError(error_msg)
            if not hasattr(mod, "qconfig"):
                raise AssertionError("Input float module must have qconfig defined")
            activation_post_process = mod.activation_post_process
            if type_before_parametrizations(mod) == nni.LinearReLU:
                mod = mod[0]
            weight_post_process = (
                mod.qconfig.weight()
                if not hasattr(mod, "weight_fake_quant")
                else mod.weight_fake_quant
            )

        if not use_precomputed_fake_quant:
            # Observer may not have been called yet
            # Observer might have been called in the previous stage via PTQ algorithm e.g. AdaRound
            weight_post_process(mod.weight)
        dtype = weight_post_process.dtype
        act_scale, act_zp = activation_post_process.calculate_qparams()
        if dtype != torch.qint8:
            raise AssertionError(
                f"Weight observer must have dtype torch.qint8, got {dtype}"
            )
        qweight = _quantize_weight(mod.weight.float(), weight_post_process)
        qlinear = cls(mod.in_features, mod.out_features, dtype=dtype)
        qlinear.set_weight_bias(qweight, mod.bias)
        qlinear.scale = float(act_scale)
        qlinear.zero_point = int(act_zp)
        return qlinear