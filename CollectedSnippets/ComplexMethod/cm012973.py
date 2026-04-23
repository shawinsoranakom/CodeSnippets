def from_float(cls, mod, use_precomputed_fake_quant=False):
        if hasattr(mod, "weight_fake_quant"):
            # assert type(mod) is cls.__QAT_MODULE, " nnq." + cls.__name__ + \
            # ".from_float only works for " + cls.__QAT_MODULE.__name__
            if type(mod) is cls._NNIQAT_CONV_BN_MODULE:
                mod.weight, mod.bias = fuse_conv_bn_weights(
                    mod.weight,
                    mod.bias,
                    mod.bn.running_mean,
                    mod.bn.running_var,
                    mod.bn.eps,
                    mod.bn.weight,
                    mod.bn.bias,
                )
            if not hasattr(mod, "activation_post_process"):
                raise AssertionError("Input QAT module must have observer attached")
            weight_post_process = mod.weight_fake_quant
            activation_post_process = mod.activation_post_process
        else:
            if type(mod) is not cls._FLOAT_MODULE:
                raise AssertionError(
                    f"nnq.{cls.__name__}.from_float only works for "
                    f"{cls._FLOAT_MODULE.__name__} but got: {type(mod).__name__}"
                )
            if not hasattr(mod, "qconfig"):
                raise AssertionError("Input float module must have qconfig defined.")
            activation_post_process = (
                None
                if not hasattr(mod, "activation_post_process")
                else mod.activation_post_process
            )
            if type(mod) in [
                cls._NNI_CONV_RELU_MODULE,
                cls._NNI_CONV_ADD_MODULE,
                cls._NNI_CONV_ADD_RELU_MODULE,
            ]:
                mod = mod[0]
            weight_post_process = mod.qconfig.weight()
        return cls.get_qconv(mod, activation_post_process, weight_post_process)