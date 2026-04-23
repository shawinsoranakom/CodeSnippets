def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a dynamic quantized module from a float module or qparams_dict

        Args:
            mod (Module): a float module, either produced by torch.ao.quantization
                          utilities or provided by the user
        """
        float_modules = [
            torch.nn.Linear,
            torch.nn.modules.linear.NonDynamicallyQuantizableLinear,
            torch.ao.nn.intrinsic.modules.fused.LinearReLU,
            torch.ao.nn.qat.dynamic.Linear,
        ]

        if type(mod) not in float_modules:
            raise AssertionError(
                "nn.quantized.dynamic.Linear.from_float only works for one of"
                + str([float_mod.__name__ for float_mod in float_modules])
                + f", got {type(mod)}"
            )
        if not hasattr(mod, "qconfig"):
            raise AssertionError("Input float module must have qconfig defined")
        if type(mod) is nni.LinearReLU:
            mod = mod[0]

        if mod.qconfig is not None and mod.qconfig.weight is not None:
            weight_observer = mod.qconfig.weight()
        else:
            # We have the circular import issues if we import the qconfig in the beginning of this file:
            # https://github.com/pytorch/pytorch/pull/24231. The current workaround is to postpone the
            # import until we need it.
            from torch.ao.quantization.qconfig import default_dynamic_qconfig

            weight_observer = default_dynamic_qconfig.weight()
        dtype = weight_observer.dtype
        if dtype not in [torch.qint8, torch.float16]:
            raise AssertionError(
                f"The only supported dtypes for dynamic quantized linear are qint8 and float16, got: {dtype}"
            )
        weight_observer(mod.weight)
        if dtype == torch.qint8:
            qweight = _quantize_weight(mod.weight.float(), weight_observer)
        elif dtype == torch.float16:
            qweight = mod.weight.float()
        else:
            raise RuntimeError(
                "Unsupported dtype specified for dynamic quantized Linear!"
            )
        qlinear = cls(mod.in_features, mod.out_features, dtype=dtype)

        qlinear.set_weight_bias(qweight, mod.bias)
        return qlinear