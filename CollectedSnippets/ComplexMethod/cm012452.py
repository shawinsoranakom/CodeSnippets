def codegen_group(self, name=None) -> str:
        self.stack.close()
        if not self.scheduled_nodes:
            return ""
        code = BracesBuffer()
        # 1. Include header files
        # TODO: support kernel profile on other platforms
        enable_kernel_profile = config.cpp.enable_kernel_profile and sys.platform in [
            "linux",
            "win32",
        ]
        if enable_kernel_profile:
            code.writelines(["#include <torch/csrc/inductor/aoti_runtime/utils.h>"])
        code.writeline("#include <torch/csrc/inductor/cpp_prefix.h>")

        # 2. Function definition
        kernel_decl_name = str(Placeholder.KERNEL_NAME) if name is None else name
        kernel_name = str(Placeholder.DESCRIPTIVE_NAME) if name is None else name
        arg_defs, _, _ = self.args.cpp_argdefs()
        arg_defs = ",\n".ljust(25).join(arg_defs)
        func_export_decl = get_export_declaration()
        inline_attr = (
            "C10_ALWAYS_INLINE_ATTRIBUTE" if config.cpp.force_inline_kernel else ""
        )
        code.writeline(
            f'extern "C" {func_export_decl} void {inline_attr} {kernel_decl_name}({arg_defs})'
        )

        # 3. Function body
        with code.indent():
            code.writeline("std::atomic<int> inductor_cpu_integer_div_error{0};")
            code.writeline(
                "inductor_cpu_integer_div_error_flag = &inductor_cpu_integer_div_error;"
            )
            if enable_kernel_profile:
                graph_id = V.graph.graph_id
                prefix = "graph_" + str(graph_id) + "_" if graph_id is not None else ""
                code.writelines(
                    [
                        (
                            "torch::aot_inductor::RAIIAtenRecordFunctionHandle "
                            f'record_{prefix + kernel_name}_("{prefix + kernel_name}", nullptr);'
                        )
                    ]
                )
            for old, new in self.args.aliases():
                code.writeline(f"auto {old} = {new};")
            code.splice(self.loops_code)
            code.writeline("inductor_cpu_integer_div_error_flag = nullptr;")
            code.writeline(
                "inductor_cpu_throw_if_integer_div_error(inductor_cpu_integer_div_error);"
            )
        return code.getvalue()