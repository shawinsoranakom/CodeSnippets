def _generate_kernel_call_helper(
        self,
        kernel_name: str,
        call_args: list[str],
        *,
        device: torch.device | None = None,
        triton: bool = True,
        arg_types: tuple[Any, ...] | None = None,
        raw_keys: tuple[Any, ...] | None = None,
        raw_args: tuple[Any, ...] | None = None,
        triton_meta: dict[str, Any] | None = None,
        inductor_meta: dict[str, Any] | None = None,
        graph_name: str = "",
        original_fxnode_name: str | None = None,
        current_stream_idx: int | None = None,
    ) -> None:
        """
        Generates MPS kernel call code. It should look something like:
        ```
        auto mps_lib_0_lambda = [&](AOTIMetalKernelFunctionHandle handle) {
            aoti_torch_mps_start_encoding(handle);
            aoti_torch_mps_set_arg_tensor(handle, 0, buf0);
            aoti_torch_mps_set_arg_tensor(handle, 1, arg0_1);
            aoti_torch_mps_set_arg_tensor(handle, 2, arg1_1);
            aoti_torch_mps_dispatch_single(handle, static_cast<uint64_t>(10LL));
        };

        std::function<void(AOTIMetalKernelFunctionHandle)> mps_lib_0_func_wrapper = mps_lib_0_lambda;
        aoti_torch_mps_run_command_block(get_mps_lib_0_handle(), aoti_torch_mps_shared_callback, &mps_lib_0_func_wrapper);
        ```
        """
        device = device or V.graph.get_current_device_or_throw()
        if device.type == "cpu":
            # Even in CppWrapperGpu, we may see cpp kernels
            return CppWrapperCpu._generate_kernel_call_helper(
                self,
                kernel_name,
                call_args,
                device=device,
                triton=triton,
                arg_types=arg_types,
                raw_keys=raw_keys,
                raw_args=raw_args,
                triton_meta=triton_meta,
                inductor_meta=inductor_meta,
            )

        assert device.type == "mps"

        assert arg_types is not None

        new_args = []
        for idx, (arg, arg_type) in enumerate(zip(call_args[:-2], arg_types[:-2])):
            if isinstance(arg_type, torch.dtype):
                new_args.append(f"aoti_torch_mps_set_arg_tensor(handle, {idx}, {arg});")
            elif arg_type in (int, sympy.core.symbol.Symbol):
                new_args.append(f"aoti_torch_mps_set_arg_int(handle, {idx}, {arg});")
            else:
                raise NotImplementedError(
                    f"Unsupported arg type {arg_type} for arg {arg} for kernel {kernel_name}"
                )

        threads, group_size = call_args[-2], call_args[-1]
        if threads is None:
            raise NotImplementedError("No threads or group_size provided")

        # Check if threads is a single value or an array-like structure
        threads_str = str(threads)
        is_single_value = (
            threads_str.startswith("{")
            and threads_str.endswith("}")
            and threads_str.count(",") == 0
        ) or not threads_str.startswith(("{", "["))

        if is_single_value:
            # Extract single value from braces if present
            if threads_str.startswith("{") and threads_str.endswith("}"):
                single_value = threads_str[1:-1].strip()  # Remove braces
            else:
                single_value = threads_str

            if group_size is None:
                new_args.append(
                    f"aoti_torch_mps_dispatch_single(handle, {single_value});"
                )
            else:
                # Extract group size value if it's also in braces
                group_size_str = str(group_size)
                if group_size_str.startswith("{") and group_size_str.endswith("}"):
                    group_size_value = group_size_str[1:-1].strip()
                else:
                    group_size_value = group_size_str
                new_args.append(
                    f"aoti_torch_mps_dispatch_single_with_group_size(handle, {single_value}, {group_size_value});"
                )
        else:
            # Handle array case - need to convert initializer list to array
            # Use kernel name to make variable names unique
            threads_var = f"{kernel_name}_threads_array"
            group_size_var = f"{kernel_name}_group_size_array"

            # Extract array size from the initializer list string
            def get_array_size(array_str: str) -> int:
                # Remove braces and whitespace
                content = array_str.strip()
                if content.startswith("{") and content.endswith("}"):
                    content = content[1:-1].strip()

                if not content:  # Empty array
                    return 0

                # Count elements by counting commas, accounting for nested structures
                depth = 0
                comma_count = 0
                for char in content:
                    if char in "({[<":
                        depth += 1
                    elif char in ")}]>":
                        depth -= 1
                    elif char == "," and depth == 0:
                        comma_count += 1

                return comma_count + 1  # Number of elements = commas + 1

            threads_size = get_array_size(threads_str)

            if group_size is None:
                new_args.append("{")
                new_args.append(f"    uint64_t {threads_var}[] = {threads};")
                new_args.append(
                    f"    aoti_torch_mps_dispatch_array(handle, {threads_var}, {threads_size});"
                )
                new_args.append("}")
            else:
                group_size_str = str(group_size)
                group_size_size = get_array_size(group_size_str)
                new_args.append("{")
                new_args.append(f"    uint64_t {threads_var}[] = {threads};")
                new_args.append(f"    uint64_t {group_size_var}[] = {group_size};")
                dispatch_args = f"handle, {threads_var}, {threads_size}, {group_size_var}, {group_size_size}"
                new_args.append(
                    f"    aoti_torch_mps_dispatch_array_with_group_size({dispatch_args});"
                )
                new_args.append("}")

        # debug printer related logic for cpp kernel type.
        debug_printer_manager = V.graph.wrapper_code.debug_printer
        debug_printer_manager.set_printer_args(
            call_args[:-2],
            kernel_name,
            None,
            None,
            "cpp",
        )
        with debug_printer_manager:
            self.write_mps_kernel_call(kernel_name, new_args)