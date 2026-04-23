def init(
        self,
        M,
        N,
        K,
        device,
        float8_dtype="e4m3fn",
        output_dtype="bfloat16",
        scaling="fp8_tensorwise",
    ):
        helpers = get_test_scaled_matmul_cuda()
        self._float8_dtype_arg = float8_dtype
        self.base_dtype = torch.bfloat16
        self.scaling = scaling
        self.float8_dtype = None

        self._set_output_dtype(output_dtype)

        if scaling == "fp8_tensorwise":
            self._init_fp8_tensorwise(M, N, K, device, helpers)
        elif scaling == "fp8_rowwise":
            self._init_fp8_rowwise(M, N, K, device, helpers)
        elif scaling == "fp8_blockwise_1x128":
            self._init_fp8_blockwise_1x128(M, N, K, device, helpers)
        elif scaling == "fp8_blockwise_128x128":
            self._init_fp8_blockwise_128x128(M, N, K, device, helpers)
        elif scaling == "mxfp8":
            self._init_mx_blockwise(M, N, K, device, mx_format="mxfp8")
        elif scaling == "mxfp4":
            self._init_mx_blockwise(M, N, K, device, mx_format="mxfp4")
        elif scaling == "nvfp4":
            self._init_nvfp4_blockwise_and_tensorwise(M, N, K, device, helpers)
        else:
            raise ValueError(f"Unsupported scaling mode: {scaling}")

        self.set_module_name("scaled_mm")