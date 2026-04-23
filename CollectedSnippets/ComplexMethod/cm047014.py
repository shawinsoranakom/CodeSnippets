def forward(ctx, x, weight, weight_scale, bias = None):
        if weight.shape[0] == weight_scale.shape[0] and (
            weight.shape[0] % 8 == 0 and weight.shape[1] % 8 == 0
        ):
            # Edit: The kernel seems to expect that the weight has dimensions divisible by 8. Otherwise it throws `RuntimeError: cutlass cannot implement`
            # One thing we can do is to pad the weight and weight scale to multiple of 8 and perform a F8F8BF16 operation.
            # I tried benchmarking that for speed but observed that dequantize+bf16 matmul is significantly faster than padding+f8f8bf16 matmul. So we'll go that route.
            # So essentially, f8f8bf16_rowise only happens when shapes are proper (no transposes) and divisible by 8.

            # quantize_fp8_per_row will squash the leading dimensions, so save the desired shape here
            output_shape = (*x.shape[:-1], -1)
            # x_quantized and x_scale are not necessarily on the same device as x, this is an issue.
            # https://github.com/pytorch/FBGEMM/blob/e08af8539c391437f447173863df0f3f6f6f1855/fbgemm_gpu/experimental/gen_ai/src/quantize/quantize.cu#L1237C3-L1237C45
            x_quantized, x_scale = torch.ops.fbgemm.quantize_fp8_per_row(
                x.view(-1, x.shape[-1]).contiguous(),
                scale_ub = getattr(weight, "input_scale_ub", None),
            )
            # moving x_quantized, x_scale here creates glibberish output ... However, if we move the output, it works
            # x_quantized, x_scale = x_quantized.to(x.device), x_scale.to(x.device)

            # The computation still happens on the device where self.weight is even if x_quantized is not on the same device as self.weight
            weight_scale_float32 = weight_scale.to(torch.float32)

            if not weight.is_contiguous():
                weight = weight.contiguous()
            if not weight_scale.is_contiguous():
                weight_scale = weight_scale.contiguous()

            output = torch.ops.fbgemm.f8f8bf16_rowwise(
                x_quantized, weight, x_scale, weight_scale_float32, use_fast_accum = True
            )
            output = output + bias if bias is not None else output
            # Hacky for now, we have the output to the device of x
            output = output.to(x.device, x.dtype)
            output = output.reshape(output_shape)
            del x_quantized, x_scale
        elif (
            weight.shape[0] != weight_scale.shape[0]
            and weight.shape[1] == weight_scale.shape[0]
        ) or (weight.shape[0] // 8 != 0 or weight.shape[1] // 8 != 0):
            # Either the weight/scale is transposed or its shape is not divisible by 8. Both cases, dequantizing is the preferred way.
            # The transpose case is generally noticed in backward pass when we do dY@W instead of @W.T as we do for forward.
            # The shape case, I noticed to happen in MLP of Qwen 2.5 VL 7B where the gate proj is of shape (3420, 1280) and 3420/8=427.5

            W_deq = weight_dequant(weight, weight_scale).T
            output = torch_matmul(x, W_deq)
            del W_deq
        else:
            raise ValueError(
                f"Shapes are incompatible {weight.shape = }, {weight_scale.shape = }, {x.shape = }"
            )

        ctx.weight = weight
        ctx.weight_scale = weight_scale
        return output