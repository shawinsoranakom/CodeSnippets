def __getattr__(self, name):
        if name == "allow_tf32":
            return torch._C._get_cublas_allow_tf32()
        elif name == "allow_fp16_reduced_precision_reduction":
            allow_reduced_precision, _ = (
                torch._C._get_cublas_allow_fp16_reduced_precision_reduction()
            )
            return allow_reduced_precision
        elif name == "allow_fp16_reduced_precision_reduction_split_k":
            _, allow_splitk = (
                torch._C._get_cublas_allow_fp16_reduced_precision_reduction()
            )
            return allow_splitk
        elif name == "allow_bf16_reduced_precision_reduction":
            allow_reduced_precision, _ = (
                torch._C._get_cublas_allow_bf16_reduced_precision_reduction()
            )
            return allow_reduced_precision
        elif name == "allow_bf16_reduced_precision_reduction_split_k":
            _, allow_splitk = (
                torch._C._get_cublas_allow_bf16_reduced_precision_reduction()
            )
            return allow_splitk
        elif name == "allow_fp16_accumulation":
            return torch._C._get_cublas_allow_fp16_accumulation()
        elif name == "fp32_precision":
            return torch._C._get_fp32_precision_getter("cuda", "matmul")
        raise AttributeError("Unknown attribute " + name)