def get_kernel_and_metadata(self) -> tuple[Kernel, Any, list[str], list[str]]:
        from triton.runtime.autotuner import Autotuner

        from torch._higher_order_ops.triton_kernel_wrap import kernel_side_table

        kernel = kernel_side_table.get_kernel(self.kernel_idx)
        configs = []
        restore_value_args: list[str] = []
        reset_to_zero_args: list[str] = []
        if isinstance(kernel, Autotuner):
            # https://github.com/triton-lang/triton/pull/5083
            # changes kernel.restore_idx to kernel.restore_value
            if hasattr(kernel, "restore_idx"):
                restore_value_args.extend(
                    kernel.fn.arg_names[i] for i in kernel.restore_idx
                )
            else:
                assert hasattr(kernel, "restore_value")
                restore_value_args.extend(kernel.restore_value)

            if hasattr(kernel, "reset_idx"):
                for i in kernel.reset_idx:
                    reset_to_zero_args.append(kernel.fn.arg_names[i])
            else:
                assert hasattr(kernel, "reset_to_zero")
                reset_to_zero_args.extend(kernel.reset_to_zero)

            configs = kernel.configs
            kernel = kernel.fn

        return kernel, configs, restore_value_args, reset_to_zero_args