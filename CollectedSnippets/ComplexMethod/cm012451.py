def define_kernel(self, src_code, nodes, kernel_args=None):
        wrapper = V.graph.wrapper_code
        if src_code in wrapper.src_to_kernel:
            kernel_name = wrapper.src_to_kernel[src_code]
        else:
            fused_name = (
                get_fused_kernel_name(nodes, config.cpp.descriptive_names)
                if config.cpp.descriptive_names
                else ""
            )
            kernel_name = "_".join(["cpp", fused_name, wrapper.next_kernel_suffix()])
            wrapper.src_to_kernel[src_code] = kernel_name
            kernel_decl_name = kernel_name if V.graph.cpp_wrapper else "kernel"
            src_code = src_code.replace(str(Placeholder.KERNEL_NAME), kernel_decl_name)
            src_code = src_code.replace(str(Placeholder.DESCRIPTIVE_NAME), kernel_name)
            # TODO(voz): Ostensibly, we should not need this. But there are cases where C++ codegen does
            # not use BracesBuffer, so we have no good indicator of a C++ buffer atm.
            src_code = src_code.replace("#pragma CMT", "//")

            # Get the lines in the source code representing the function definition,
            # excluding the first line including cpp_prefix.h.
            first_char = src_code.rfind('extern "C"')
            last_char = src_code.find(")", first_char)
            if _IS_WINDOWS:
                # get_export_declaration introduced one more ')' in Windows
                last_char = src_code.find(")", last_char + 1)
            kernel_definition = f"{src_code[first_char : last_char + 1]};\n"

            compile_wrapper = IndentedBuffer()
            args = self.kernel_group.args if kernel_args is None else kernel_args
            _, _, arg_types = args.cpp_argdefs()
            if not V.graph.cpp_wrapper:
                compile_wrapper.writeline(
                    f"async_compile.cpp_pybinding({arg_types!r}, r'''"
                )
            compile_wrapper.splice(src_code, strip=True)
            if not V.graph.cpp_wrapper:
                compile_wrapper.writeline("''')")
            wrapper.define_kernel(
                kernel_name,
                compile_wrapper.getvalue(),
                gpu=False,
                cpp_definition=kernel_definition,
            )
        return kernel_name