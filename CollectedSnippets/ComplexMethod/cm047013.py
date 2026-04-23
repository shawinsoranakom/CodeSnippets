def forward(ctx, X, weight, weight_scale):
        m, n = weight.shape

        # Save original scale for backward (before any transformation)
        original_weight_scale = weight_scale

        # Handle per-tensor quantization: expand scalar to block scale shape
        if weight_scale.numel() == 1:
            block_size = [128, 128]
            # Expand scalar to (ceil(m/128), ceil(n/128)) - same value for all blocks
            num_blocks_m = triton.cdiv(m, block_size[0])
            num_blocks_n = triton.cdiv(n, block_size[1])
            weight_scale = weight_scale.expand(num_blocks_m, num_blocks_n).contiguous()
        else:
            # Block quantization path
            p, q = weight_scale.shape
            block_size = getattr(weight, "block_size", None) or getattr(
                weight_scale, "block_size", [128, 128]
            )
            assert block_size is not None, "block_size is not set"
            if triton.cdiv(m, block_size[0]) != p or triton.cdiv(n, block_size[1]) != q:
                if (
                    triton.cdiv(m, block_size[0]) == q
                    and triton.cdiv(n, block_size[1]) == p
                ):
                    weight_scale = weight_scale.T
                    original_weight_scale = weight_scale  # Update for transposed case
                else:
                    raise ValueError(
                        f"Weight shape {weight.shape} and scales shape {weight_scale.shape} is not compatible with block size {block_size}"
                    )

        if not weight.is_contiguous():
            weight = weight.contiguous()

        # Quantize input and run FP8 matmul
        qinput, scale = act_quant(X, block_size[1])
        output = fp8_block_matmul(
            qinput,
            weight,
            scale,
            weight_scale,
            block_size,
            output_dtype = X.dtype,
        )
        ctx.weight = weight
        ctx.weight_scale = original_weight_scale  # Save original for backward
        return output.to(X.dtype)