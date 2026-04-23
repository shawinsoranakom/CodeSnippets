def backward(ctx, grad_output):
        compute_dtype = ctx.compute_dtype
        grad_2d = grad_output.flatten(0, -2).to(compute_dtype)

        # Value casting — only difference between fp8 and non-fp8 paths
        if ctx.fp8_bwd:
            weight, = ctx.saved_tensors
            # Wrap as FP8 QuantizedTensors → torch.mm dispatches to _scaled_mm
            grad_mm = QuantizedTensor.from_float(grad_2d, "TensorCoreFP8E5M2Layout")
            if isinstance(weight, QuantizedTensor) and weight._layout_cls.startswith("TensorCoreFP8"):
                weight_mm = weight
            elif isinstance(weight, QuantizedTensor):
                weight_mm = QuantizedTensor.from_float(weight.dequantize().to(compute_dtype), "TensorCoreFP8E4M3Layout")
            else:
                weight_mm = QuantizedTensor.from_float(weight.to(compute_dtype), "TensorCoreFP8E4M3Layout")
            input_mm = ctx.q_input
        else:
            input_float, weight = ctx.saved_tensors
            # Standard tensors → torch.mm does regular matmul
            grad_mm = grad_2d
            if isinstance(weight, QuantizedTensor):
                weight_mm = weight.dequantize().to(compute_dtype)
            else:
                weight_mm = weight.to(compute_dtype)
            input_mm = input_float.flatten(0, -2).to(compute_dtype) if ctx.weight_requires_grad else None

        # Computation — same for both paths, dispatch handles the rest
        grad_input = torch.mm(grad_mm, weight_mm)
        if len(ctx.input_shape) > 2:
            grad_input = grad_input.unflatten(0, ctx.input_shape[:-1])

        grad_weight = None
        if ctx.weight_requires_grad:
            grad_weight = torch.mm(grad_mm.t(), input_mm)

        grad_bias = None
        if ctx.has_bias:
            grad_bias = grad_2d.sum(dim=0)

        return grad_input, grad_weight, grad_bias, None, None, None