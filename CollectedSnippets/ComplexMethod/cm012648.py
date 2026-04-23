def set_printer_args(
        self,
        args_to_print_or_save: list[str],
        kernel_name: str,
        arg_signatures: list[type] | None,
        kernel,
        kernel_type=None,
    ):
        # Note: MultiKernel debug printing is not supported for now
        if isinstance(kernel, MultiKernel):
            log.info(
                "MultiKernel type is not supported in AOTI debug printer tool yet."
            )
            self.debug_printer_level = IntermediateValueDebuggingLevel.OFF

        self.kernel_type = kernel_type
        # Note: if the kernel type is an extern kernel (or cpp kernel), we do a special handling to
        # get the list of args_to_print_or_save
        # TODO: Find a more reliable way to detect kernel args types to print for extern kernel calls
        if kernel_type == "extern":
            args_to_print_or_save_extern = [
                arg
                for arg in args_to_print_or_save
                if isinstance(arg, str) and arg.startswith(("buf", "arg"))
            ]
            self.args_to_print_or_save = args_to_print_or_save_extern
        elif kernel_type == "cpp":
            self.args_to_print_or_save = [
                (
                    f"copy_arrayref_tensor_to_tensor({arg})"
                    if self.use_array_ref
                    else arg
                )
                for arg in args_to_print_or_save
                if isinstance(arg, str) and arg.startswith(("buf", "arg"))
            ]
        else:
            self.args_to_print_or_save = args_to_print_or_save
        self.kernel_name = kernel_name
        self.arg_signatures = arg_signatures
        self.kernel = kernel