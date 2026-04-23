def codegen_define(self, kernel: CppTemplateKernel) -> str:
        block_m, block_n, block_k = self.register_blocking
        assert block_m % 16 == 0, "Only support block_m % 16 == 0 for AMX"
        assert block_n % 16 == 0, "Only support block_n % 16 == 0 for AMX"
        if self.input_dtype in [torch.uint8, torch.int8]:
            assert block_k == 64, "Only support block_k = 64 for AMX INT8"
        else:
            assert block_k == 32, "Only support block_k = 32 for AMX Bfloat16/Float16"
        num_columns = block_n // 16
        options = {
            "declare_kernel": self.get_kernel_declaration(),
            "use_cached_dequantized_B": (
                self.input_dtype == torch.bfloat16
                and self.input2_dtype in [torch.int8, torch.uint8]
            ),
            "kernel": kernel,
            "block_m": block_m,
            "block_n": block_n,
            "block_k": block_k,
            "num_columns": num_columns,
            "restrict_keyword": get_restrict_keyword(),
            **self.get_common_options(),
        }
        result = ""
        for num_rows in range(block_m, 0, -16):
            amx_kernel_options = {**options, "num_rows": num_rows}
            result += KernelTemplate._template_from_string(self.TEMPLATE_KERNEL).render(
                amx_kernel_options
            )
        result += KernelTemplate._template_from_string(self.TEMPLATE_ENTRY).render(
            options
        )
        return result