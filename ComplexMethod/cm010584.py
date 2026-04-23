def add_qlinear(self, node):
        if node.inputsSize() != 4:
            raise AssertionError(
                f"expected node.inputsSize() == 4, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )
        (
            jit_input,
            jit_packed_weight,
            jit_scale,
            jit_zero_point,
        ) = node.inputs()

        input_id, input_oper = self.get_tensor_operand_by_jitval_fixed_size(jit_input)
        # TODO: Support automatic reshape
        if len(input_oper.shape) != 2:
            raise AssertionError(
                f"expected len(input_oper.shape) == 2, got {len(input_oper.shape)}"
            )

        _, out_scale = self.get_constant_value(jit_scale, "FloatType")
        _, out_zero_point = self.get_constant_value(jit_zero_point, "IntType")
        weight_ctype, packed_weight = self.get_constant_value(jit_packed_weight)
        if weight_ctype.name() != "LinearPackedParamsBase":
            raise AssertionError(
                f"expected weight_ctype LinearPackedParamsBase, got {weight_ctype.name()}"
            )
        raw_weight, raw_bias = packed_weight.__getstate__()[0]
        if raw_bias is None:
            raise AssertionError("raw_bias must not be None")

        if len(raw_weight.shape) != 2:
            raise AssertionError(
                f"expected len(raw_weight.shape) == 2, got {len(raw_weight.shape)}"
            )
        if len(raw_bias.shape) != 1:
            raise AssertionError(
                f"expected len(raw_bias.shape) == 1, got {len(raw_bias.shape)}"
            )
        if raw_bias.shape[0] != raw_weight.shape[0]:
            raise AssertionError(
                f"raw_bias.shape[0] {raw_bias.shape[0]} != raw_weight.shape[0] {raw_weight.shape[0]}"
            )
        if raw_weight.shape[1] != input_oper.shape[1]:
            raise AssertionError(
                f"raw_weight.shape[1] {raw_weight.shape[1]} != input_oper.shape[1] {input_oper.shape[1]}"
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
        bias_scale = input_oper.scale * weight_scale
        int_bias = torch.quantize_per_tensor(raw_bias, bias_scale, 0, torch.qint32)
        bias_id = self.add_tensor_operand_for_weight(int_bias)

        multiplier = input_oper.scale * weight_scale / out_scale
        if multiplier <= 0:
            raise AssertionError(f"expected multiplier > 0, got {multiplier}")
        if multiplier >= 1:
            raise Exception(  # noqa: TRY002
                "Quantized convolution multiplier is greater than 1.  "
                "This is supported by NNAPI, but not by most hardware backends.  "
                "Try training a model without quantization-aware training.  "
            )

        # TODO: Transform at load time to share weights with CPU model.
        nnapi_weight_tensor = unsigned_weight.contiguous()
        weight_id = self.add_tensor_operand_for_weight(nnapi_weight_tensor)
        weight_oper = self.operands[weight_id]

        out_shape = (input_oper.shape[0], weight_oper.shape[0])
        out_oper = input_oper._replace(
            shape=out_shape,
            scale=out_scale,
            zero_point=out_zero_point,
        )

        inputs = [None] * 4
        inputs[0] = input_id
        inputs[1] = weight_id
        inputs[2] = bias_id
        inputs[3] = self.add_immediate_int_scalar(NNAPI_FuseCode.FUSED_NONE)

        outputs = [None] * 1
        outputs[0] = self.add_tensor_operand(node.outputsAt(0), out_oper)

        self.add_operation(NNAPI_OperationCode.FULLY_CONNECTED, inputs, outputs)