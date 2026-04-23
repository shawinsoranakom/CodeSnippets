def init_variable(
        self,
        variable: Union["TraceableTritonKernelWrapper", "TritonKernelVariable"],
        kernel: "TritonKernelType",
        kernel_idx: int | None,
        grid: Optional["TritonGridType"],
    ) -> None:
        from triton.runtime.autotuner import Autotuner

        if kernel is None:
            raise AssertionError("kernel cannot be None")

        variable.kernel = kernel
        variable.kernel_idx = kernel_side_table.add_kernel(kernel)

        if kernel_idx is not None and variable.kernel_idx != kernel_idx:
            raise AssertionError(
                f"kernel_idx mismatch: expected {kernel_idx}, got {variable.kernel_idx}"
            )

        # pyrefly: ignore [bad-assignment]
        variable.grid = grid

        if isinstance(kernel, Autotuner):
            import torch
            import torch._dynamo

            # We only support configs, keys, and restore_value arguments
            # of triton.autotune. Make sure other arguments are defaulted.
            defaults = inspect.signature(Autotuner.__init__).parameters
            # Newer version of triton change attribute name from warmup to num_warmup and rep to num_rep.
            # The call to get_first_attr is to maintain backward-compatibility.

            def defaults_ok(
                attr: str, alternates: tuple[str, ...], values: tuple[Any, ...]
            ) -> bool:
                if attr not in defaults:
                    return True
                value = torch._dynamo.utils.get_first_attr(kernel, attr, *alternates)
                if value == defaults[attr].default:
                    return True
                return value in values

            if (
                not torch._inductor.config.unsafe_ignore_unsupported_triton_autotune_args
                and (
                    not defaults_ok("num_warmups", ("warmup",), (25, None))
                    or not defaults_ok("num_reps", ("rep",), (100, None))
                    or not defaults_ok("use_cuda_graph", (), (False,))
                )
            ):
                self.raise_unsupported(
                    "Only configs, keys, restore_value, and reset_to_zero are supported for triton.autotune"
                )
            if (
                not torch._inductor.config.unsafe_ignore_unsupported_triton_autotune_args
                and (
                    # pre_hook requires running arbitrary code at runtime, which we cannot handle at this time
                    # https://github.com/pytorch/pytorch/issues/139059
                    # we can't support pre_hook or post_hook in user defined triton kernels at the moment,
                    # as they require the ability to execute code at runtime (AOTI can't support this)
                    (
                        hasattr(kernel, "user_defined_pre_hook")
                        and kernel.user_defined_pre_hook is not False
                    )
                    or (
                        hasattr(kernel, "user_defined_post_hook")
                        and kernel.user_defined_post_hook is not False
                    )
                    or (
                        # Check Config passed to autotuner in configs
                        any(cfg.pre_hook is not None for cfg in kernel.configs)
                    )
                )
            ):
                self.raise_unsupported(
                    "pre_hook and post_hook are not supported in triton.Autotune or triton.Config"
                )