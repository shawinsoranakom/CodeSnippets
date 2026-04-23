def add_conv2d_common(
        self,
        jit_out,
        out_scale,
        out_zero_point,
        jit_image,
        weight_tensor,
        bias_id,
        args,
        transpose,
        fuse_code,
    ):
        image_id, image_oper = self.get_tensor_operand_by_jitval(jit_image)
        in_c = image_oper.shape[1]

        if args.group == 1:
            # Full convolution
            depthwise = False
            if transpose:
                weight_permutation = (1, 2, 3, 0)
            else:
                weight_permutation = (0, 2, 3, 1)
        elif args.group == in_c:
            # Depthwise convolution
            depthwise = True
            weight_permutation = (1, 2, 3, 0)
        else:
            raise Exception("Group convolution not supported yet.")  # noqa: TRY002

        # TODO: Transform at load time to share weights with CPU model.
        nnapi_weight_tensor = weight_tensor.permute(*weight_permutation).contiguous()
        weight_id = self.add_tensor_operand_for_weight(nnapi_weight_tensor)
        weight_oper = self.operands[weight_id]

        bias_oper = self.operands[bias_id]

        if image_oper.op_type == NNAPI_OperandCode.TENSOR_FLOAT32:
            if weight_oper.op_type != NNAPI_OperandCode.TENSOR_FLOAT32:
                raise AssertionError(
                    f"expected weight_oper TENSOR_FLOAT32, got {weight_oper.op_type}"
                )
            if bias_oper.op_type != NNAPI_OperandCode.TENSOR_FLOAT32:
                raise AssertionError(
                    f"expected bias_oper TENSOR_FLOAT32, got {bias_oper.op_type}"
                )
        elif image_oper.op_type == NNAPI_OperandCode.TENSOR_QUANT8_ASYMM:
            if weight_oper.op_type != NNAPI_OperandCode.TENSOR_QUANT8_ASYMM:
                raise AssertionError(
                    f"expected weight_oper TENSOR_QUANT8_ASYMM, got {weight_oper.op_type}"
                )
            if bias_oper.op_type != NNAPI_OperandCode.TENSOR_INT32:
                raise AssertionError(
                    f"expected bias_oper TENSOR_INT32, got {bias_oper.op_type}"
                )
            if not approx_equal(image_oper.scale * weight_oper.scale, bias_oper.scale):
                raise AssertionError(
                    f"scale mismatch: image*weight scale {image_oper.scale * weight_oper.scale} != bias scale {bias_oper.scale}"
                )
            if bias_oper.zero_point != 0:
                raise AssertionError(
                    f"expected bias_oper.zero_point == 0, got {bias_oper.zero_point}"
                )
        else:
            raise Exception(  # noqa: TRY002
                f"Unsupported input type for conv2d: {image_oper.op_type}"
            )

        if len(image_oper.shape) != 4:
            raise AssertionError(
                f"expected len(image_oper.shape) == 4, got {len(image_oper.shape)}"
            )
        if len(weight_oper.shape) != 4:
            raise AssertionError(
                f"expected len(weight_oper.shape) == 4, got {len(weight_oper.shape)}"
            )
        if len(bias_oper.shape) != 1:
            raise AssertionError(
                f"expected len(bias_oper.shape) == 1, got {len(bias_oper.shape)}"
            )

        if depthwise:
            # Depthwise convolution
            one, _kern_h, _kern_w, out_c = weight_oper.shape
            if one != 1:
                raise AssertionError(f"expected weight_oper.shape[0] == 1, got {one}")
            if out_c % in_c != 0:
                raise AssertionError(f"out_c {out_c} must be divisible by in_c {in_c}")
            channel_multiplier = out_c // in_c
            if channel_multiplier != 1:
                raise AssertionError(
                    f"channel_multiplier must be 1, got {channel_multiplier}"
                )
            if out_c != in_c:
                raise AssertionError(f"out_c {out_c} != in_c {in_c}")
        else:
            # Full convolution
            out_c, _kern_h, _kern_w, kern_d = weight_oper.shape
            if kern_d != in_c:
                raise AssertionError(f"kern_d {kern_d} != in_c {in_c}")

        if out_c != bias_oper.shape[0]:
            raise AssertionError(
                f"out_c {out_c} != bias_oper.shape[0] {bias_oper.shape[0]}"
            )

        use_nchw = image_oper.use_nchw()

        if depthwise:
            num_args = 12
            opcode = NNAPI_OperationCode.DEPTHWISE_CONV_2D
        else:
            num_args = 11
            if transpose:
                opcode = NNAPI_OperationCode.TRANSPOSE_CONV_2D
            else:
                opcode = NNAPI_OperationCode.CONV_2D

        inputs = [None] * num_args
        inputs[0] = image_id
        inputs[1] = weight_id
        inputs[2] = bias_id
        inputs[3] = self.add_immediate_int_scalar(args.pad_l)
        inputs[4] = self.add_immediate_int_scalar(args.pad_r)
        inputs[5] = self.add_immediate_int_scalar(args.pad_t)
        inputs[6] = self.add_immediate_int_scalar(args.pad_b)
        inputs[7] = self.add_immediate_int_scalar(args.stride_w)
        inputs[8] = self.add_immediate_int_scalar(args.stride_h)
        if depthwise:
            inputs[9] = self.add_immediate_int_scalar(1)
            inputs[10] = self.add_immediate_int_scalar(fuse_code)
            inputs[11] = self.add_immediate_bool_scalar(use_nchw)
        else:
            inputs[9] = self.add_immediate_int_scalar(fuse_code)
            inputs[10] = self.add_immediate_bool_scalar(use_nchw)

        outputs = [None] * 1
        out_shape = get_conv_pool_shape(image_oper.shape, args, out_c, transpose)
        out_oper = image_oper._replace(
            shape=out_shape,
            scale=out_scale,
            zero_point=out_zero_point,
        )
        out_id = self.add_tensor_operand(jit_out, out_oper)
        self._handle_conv_pool_flexible_input(out_id, jit_image, args, transpose)

        outputs[0] = out_id
        self.add_operation(opcode, inputs, outputs)