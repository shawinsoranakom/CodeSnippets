def codegen_intermediate_tensor_value_print(
        self,
        args_to_print,
        kernel_name,
        before_launch=True,
        arg_signatures: list[type] | None = None,
    ) -> None:
        launch_prefix = "before_launch" if before_launch else "after_launch"

        # if the debug printing level is PRINT_KERNEL_NAMES_ONLY
        # we only print the kernel name to the console
        if (
            self.debug_printer_level
            == IntermediateValueDebuggingLevel.PRINT_KERNEL_NAMES_ONLY
        ):
            if V.graph.cpp_wrapper:
                V.graph.wrapper_code.writeline(
                    f'printf("[ {launch_prefix}: {kernel_name} ]\\n");'
                )
            return

        if self.debug_printer_level != IntermediateValueDebuggingLevel.PRINT_ONLY:
            return
        for i, arg in enumerate(args_to_print):
            # when debug printing is enabled i.e. IntermediateValueDebuggingLevel.PRINT_ONLY,
            # check if filtered kernel name list is provided
            if (
                len(self.filtered_kernel_names_to_print) > 0
                and kernel_name.lower() not in self.filtered_kernel_names_to_print
            ):
                continue
            if V.graph.cpp_wrapper:
                if arg_signatures is not None and isinstance(
                    arg_signatures[i], torch_dtype
                ):
                    # infer from the arg data type (has torch.dtype) to see if it is a tensor type
                    V.graph.wrapper_code.writeline(
                        f'aoti_torch_print_tensor_handle({arg}, "{launch_prefix} - {kernel_name} - {arg}");'
                    )
                elif arg_signatures is not None and isinstance(
                    arg_signatures[i],
                    (
                        type(torch._inductor.codegen.wrapper.SymbolicCallArg),
                        type(int),
                        type(float),
                        type(bool),
                    ),
                ):
                    V.graph.wrapper_code.writeline(
                        f'printf("[  {launch_prefix} - {kernel_name} - {arg}: %ld  ]", {arg}); printf("\\\\n");'
                    )
                else:
                    if arg_signatures is None and self.kernel_type in ("cpp", "extern"):
                        V.graph.wrapper_code.writeline(
                            f'aoti_torch_print_tensor_handle({arg}, "{launch_prefix} - {kernel_name} - {arg}");'
                        )
            else:
                V.graph.wrapper_code.writeline(
                    f'_print_debugging_tensor_value_info("inductor: {launch_prefix} - {kernel_name} - {arg}", {arg})'
                )