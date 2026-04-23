def check_can_launch() -> _KernelType:
            if triton_meta.get("device_type") not in ("cuda", "xpu", "hip"):
                raise CannotStaticallyLaunchKernel("Non-cuda/XPU/ROCm device")

            if triton_meta.get("device_type") == "xpu" and XPU_KERNEL_FORMAT == "spv":
                raise CannotStaticallyLaunchKernel(
                    "Static XPU Triton kernel launch does not support SPIR-V kernel."
                )

            if torch._inductor.config.cpp_wrapper:
                # If we're running with cpp wrapper, it doesn't
                # make sense to statically compile since everything
                # is codegenned anyway
                raise CannotStaticallyLaunchKernel("Cpp wrapper enabled")

            if (
                heuristic_type == HeuristicType.USER_AUTOTUNE
                and not torch._inductor.config.static_launch_user_defined_triton_kernels
            ):
                # Don't support user defined triton kernels yet
                raise CannotStaticallyLaunchKernel("User defined triton kernel")

            if inductor_meta.get("store_cubin"):
                # Requires storing the entire binary
                raise CannotStaticallyLaunchKernel("store_cubin is enabled")

            if getattr(kernel.metadata, "launch_pdl", False) or getattr(
                kernel.metadata, "launch_cooperative_grid", False
            ):
                raise CannotStaticallyLaunchKernel(
                    "static launch does not support launch attributes"
                )

            binary_ext = GPU_KERNEL_BIN_EXTS.get(
                triton_meta.get("device_type"), ".cubin"
            )
            cubin_location = os.path.join(
                triton_cache_dir(triton_meta.get("device", 0)),
                triton_hash_to_path_key(kernel.hash),
                f"{kernel.src.fn.__name__}{binary_ext}",
            )

            if not os.path.exists(cubin_location):
                raise CannotStaticallyLaunchKernel(
                    f"Cubin path not found: {cubin_location}"
                )

            else:
                kernel._cubin_path = cubin_location

            try:
                static_kernel = statically_launched_kernel_by_device(
                    kernel, triton_meta.get("device_type")
                )
            except NotImplementedError as e:
                raise CannotStaticallyLaunchKernel(f"NotImplemented: {str(e)}") from e

            return static_kernel