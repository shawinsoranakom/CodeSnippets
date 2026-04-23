def _check_scaled_mm_sizes(
    self: torch.Tensor,
    mat2: torch.Tensor,
    scale_a: torch.Tensor,
    scale_b: torch.Tensor,
    bias: torch.Tensor | None = None,
    scale_result: torch.Tensor | None = None,
    out_dtype: torch.dtype | None = None,
    use_fast_accum: bool = False,
):
    def is_fp8_or_fp4_type(dtype):
        return dtype in (
            torch.float8_e4m3fn,
            torch.float8_e5m2,
            torch.float8_e4m3fnuz,
            torch.float8_e5m2fnuz,
            torch.float4_e2m1fn_x2,
        )

    torch._check(
        self.dim() == 2 and mat2.dim() == 2,
        lambda: f"Inputs must be 2D but got self.dim()={self.dim()} and mat2.dim()={mat2.dim()}",
    )
    torch._check(
        is_fp8_or_fp4_type(self.dtype) and is_fp8_or_fp4_type(mat2.dtype),
        lambda: f"Expected both inputs to be fp8 or fp4 types but got self.dtype={self.dtype} and mat2.dtype={mat2.dtype}",
    )

    if (
        device_hint(self) == "cuda"
        or device_hint(self) == "xpu"
        or device_hint(self) == "cpu"
    ):

        def is_row_major(stride):
            return stride[0] > stride[1] and stride[1] == 1

        def is_col_major(stride):
            return stride[0] == 1 and stride[1] > 1

        def has_zero_dim(tensor_2d):
            return tensor_2d.size(0) == 0 or tensor_2d.size(1) == 0

        if device_hint(self) != "cpu":
            torch._check(
                is_row_major(self.stride()) or has_zero_dim(self),
                lambda: f"self must be row_major, got stride {self.stride()}",
            )
            torch._check(
                is_col_major(mat2.stride()) or has_zero_dim(mat2),
                lambda: f"mat2 must be col_major, got stride {mat2.stride()}",
            )
            torch._check(
                self.size(1) % 16 == 0,
                lambda: f"Expected self.size(1) to be divisible by 16, but got self.size(1)={self.size(1)}",
            )
            torch._check(
                mat2.size(0) % 16 == 0 and mat2.size(1) % 16 == 0,
                lambda: f"Expected both dimensions of mat2 to be divisible by 16 but got {mat2.shape}",
            )

        # determine scaling type and check input dimensions (refer to Blas.cpp op)

        m, _k = self.shape
        n = mat2.size(1)

        is_blockwise_scaling = (
            (
                scale_a.dtype == torch.float8_e8m0fnu
                and scale_b.dtype == torch.float8_e8m0fnu
            )
            or (
                scale_a.dtype == torch.float8_e4m3fn
                and scale_b.dtype == torch.float8_e4m3fn
            )
        )  # note: this applies to blockwise scaling for non-FP8 types (FP8 accepts FP32 scales)

        if scale_a.numel() == 1 and scale_b.numel() == 1:
            # tensorwise scaling
            torch._check(
                scale_a.dtype == torch.float32 and scale_b.dtype == torch.float32,
                lambda: "For tensorwise scaling, both scale_a and scale_b must be float (fp32) tensors.",
            )
        elif is_blockwise_scaling:
            # blockwise scaling

            if scale_a.dtype == torch.float8_e4m3fn:
                # NVIDIA's nvfp4 recipe:
                # * block size is 16 elements packed (32 unpacked)
                # * _k needs to be translated to the unpacked version
                block_size_k = 16
                _k = _k * 2
            else:
                block_size_k = 32
                if self.dtype == torch.float4_e2m1fn_x2:
                    _k = _k * 2

            block_size_mn = 128

            num_k_blocks = ceil_div(_k, block_size_k)
            padded_num_k_blocks = ceil_div(num_k_blocks, 4) * 4

            expected_a_size = (
                block_size_mn * ceil_div(m, block_size_mn) * padded_num_k_blocks
            )
            expected_b_size = (
                block_size_mn * ceil_div(n, block_size_mn) * padded_num_k_blocks
            )

            if (
                scale_a.numel() == expected_a_size
                and scale_b.numel() == expected_b_size
            ):
                torch._check(
                    scale_a.is_contiguous(),
                    lambda: "scale_a must be contiguous",
                )
                torch._check(
                    scale_b.is_contiguous(),
                    lambda: "scale_b must be contiguous",
                )
            else:
                torch._check(
                    False,
                    lambda: (
                        "Invalid blockwise scaling configuration. "
                        f"For blockwise scaling, scale_a should have {expected_a_size} elements, got {scale_a.numel()}, "
                        f"scale_b should have {expected_b_size} elements, got {scale_b.numel()}."
                    ),
                )
        else:
            torch._check(
                scale_a.dtype == torch.float32 and scale_b.dtype == torch.float32,
                lambda: "For rowwise scaling, both scale_a and scale_b must be float (fp32) tensors.",
            )
            # for rowwise scaling, enforce 2D input tensors
            torch._check(
                scale_a.dim() == 2 and scale_b.dim() == 2,
                lambda: f"For non-tensorwise scaling, scale tensors must be 2D, but got {scale_a.dim()=} and {scale_b.dim()=}",
            )

            if (
                scale_a.size(0) == m
                and scale_a.size(1) == 1
                and scale_b.size(0) == 1
                and scale_b.size(1) == n
            ):
                # rowwise scaling
                torch._check(
                    scale_a.is_contiguous() and scale_b.is_contiguous(),
                    lambda: "Both scale_a and scale_b must be contiguous for rowwise scaling.",
                )
            elif (
                scale_a.size(0) == m
                and scale_a.size(1) == scale_b.size(0) == ceil_div(_k, 128)
                and scale_b.size(1) == ceil_div(n, 128)
            ):
                # (BlockWise1x128, BlockWise128x128)
                pass  # do nothing, but do not error
            elif (
                scale_a.size(0) == m
                and scale_a.size(1) == scale_b.size(0) == ceil_div(_k, 128)
                and scale_b.size(1) == n
            ):
                # (BlockWise1x128, BlockWise1x128)
                pass  # do nothing, but do not error
            elif (
                scale_a.size(0) == ceil_div(m, 128)
                and scale_a.size(1) == scale_b.size(0) == ceil_div(_k, 128)
                and scale_b.size(1) == n
            ):
                # (BlockWise128x128, BlockWise1x128)
                pass  # do nothing, but do not error
            else:
                # does not match any valid scaling type
                torch._check(
                    False,
                    lambda: (
                        "Invalid scaling configuration. "
                        "For tensorwise scaling, both scales should be scalar. "
                        f"For rowwise scaling, scale_a should be ({m}, 1), scale_b should be (1, {n}). "
                        f"For (BlockWise1x128, BlockWise128x128), scale_a should be ({m}, {ceil_div(_k, 128)}), "
                        + f"scale_b should be ({ceil_div(_k, 128)}, {ceil_div(n, 128)}). "
                        f"For (BlockWise1x128, BlockWise1x128), scale_a should be ({m}, {ceil_div(_k, 128)}), "
                        + f"scale_b should be ({ceil_div(_k, 128)}, {n}). "
                        f"For (BlockWise128x128, BlockWise1x128), scale_a should be ({ceil_div(m, 128)}, {ceil_div(_k, 128)}), "
                        + f"scale_b should be ({ceil_div(_k, 128)}, {n}). "
                        f"Got scale_a.size()=({scale_a.size(0)}, {scale_a.size(1)}) "
                        f"and scale_b.size()=({scale_b.size(0)}, {scale_b.size(1)})"
                    ),
                )

    _out_dtype = out_dtype if out_dtype is not None else self.dtype
    return torch.empty(self.size(0), mat2.size(1), dtype=_out_dtype, device=self.device)