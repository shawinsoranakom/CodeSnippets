def forward(ctx, input_float, weight, bias, layout_type, input_scale, compute_dtype):
        input_shape = input_float.shape
        inp = input_float.detach().flatten(0, -2)  # zero-cost view to 2D

        # Quantize input for forward (same layout as weight)
        if layout_type is not None:
            q_input = QuantizedTensor.from_float(inp, layout_type, scale=input_scale)
        else:
            q_input = inp

        w = weight.detach() if weight.requires_grad else weight
        b = bias.detach() if bias is not None and bias.requires_grad else bias

        output = torch.nn.functional.linear(q_input, w, b)

        # Unflatten output to match original input shape
        if len(input_shape) > 2:
            output = output.unflatten(0, input_shape[:-1])

        # Save for backward
        ctx.input_shape = input_shape
        ctx.has_bias = bias is not None
        ctx.compute_dtype = compute_dtype
        ctx.weight_requires_grad = weight.requires_grad
        ctx.fp8_bwd = comfy.model_management.training_fp8_bwd

        if ctx.fp8_bwd:
            # Cache FP8 quantized input — half the memory of bf16
            if isinstance(q_input, QuantizedTensor) and layout_type.startswith('TensorCoreFP8'):
                ctx.q_input = q_input  # already FP8, reuse
            else:
                # NVFP4 or other layout — quantize input to FP8 for backward
                ctx.q_input = QuantizedTensor.from_float(inp, "TensorCoreFP8E4M3Layout")
            ctx.save_for_backward(weight)
        else:
            ctx.q_input = None
            ctx.save_for_backward(input_float, weight)

        return output