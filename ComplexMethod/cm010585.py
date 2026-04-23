def add_qconv2d(self, node, fuse_code, transpose=False):
        if node.inputsSize() != 4:
            raise AssertionError(
                f"expected node.inputsSize() == 4, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        (
            jit_image,
            jit_packed_weight,
            jit_scale,
            jit_zero_point,
        ) = node.inputs()

        _, out_scale = self.get_constant_value(jit_scale, "FloatType")
        _, out_zero_point = self.get_constant_value(jit_zero_point, "IntType")
        weight_ctype, packed_weight = self.get_constant_value(jit_packed_weight)
        if weight_ctype.name() != "Conv2dPackedParamsBase":
            raise AssertionError(
                f"expected weight_ctype Conv2dPackedParamsBase, got {weight_ctype.name()}"
            )
        (
            pack_version,
            tensors,
            opt_tensors,
        ) = packed_weight.__getstate__()[0]
        if pack_version != "2":
            raise AssertionError(f"expected pack_version '2', got {pack_version!r}")
        packed_config, raw_weight = tensors
        (raw_bias,) = opt_tensors
        if raw_bias is None:
            raise AssertionError("raw_bias must not be None")
        args = self.get_conv_pool_args_2d_from_pack(
            raw_weight.shape[2:4], packed_config
        )

        if raw_weight.qscheme() != torch.per_tensor_affine:
            raise AssertionError(
                f"expected raw_weight.qscheme() per_tensor_affine, got {raw_weight.qscheme()}"
            )
        if raw_weight.dtype == torch.quint8:
            unsigned_weight = raw_weight
        else:
            if raw_weight.dtype != torch.qint8:
                raise AssertionError(
                    f"expected raw_weight.dtype qint8, got {raw_weight.dtype}"
                )
            unsigned_weight = torch._make_per_tensor_quantized_tensor(
                (raw_weight.int_repr().int() + 128).to(torch.uint8),
                scale=raw_weight.q_scale(),
                zero_point=raw_weight.q_zero_point() + 128,
            )
        weight_scale = unsigned_weight.q_scale()
        _, image_oper = self.get_tensor_operand_by_jitval(jit_image)
        bias_scale = image_oper.scale * weight_scale
        int_bias = torch.quantize_per_tensor(raw_bias, bias_scale, 0, torch.qint32)
        bias_id = self.add_tensor_operand_for_weight(int_bias)

        multiplier = image_oper.scale * weight_scale / out_scale
        if multiplier <= 0:
            raise AssertionError(f"expected multiplier > 0, got {multiplier}")
        if multiplier >= 1:
            raise Exception(  # noqa: TRY002
                "Quantized convolution multiplier is greater than 1.  "
                "This is supported by NNAPI, but not by most hardware backends.  "
                "Try training a model without quantization-aware training.  "
            )

        return self.add_conv2d_common(
            node.outputsAt(0),
            out_scale,
            out_zero_point,
            jit_image,
            unsigned_weight,
            bias_id,
            args,
            transpose,
            fuse_code,
        )