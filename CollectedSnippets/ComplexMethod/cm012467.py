def codegen_kernel(self, name: str = "generated_kernel") -> str:
        """Called at the end to generate a final kernel string"""
        self.codegen_body()
        code = IndentedBuffer()
        fn_name = name

        if V.graph.cpp_wrapper:
            code.writeline('(R"MTL(')
        else:
            code.writeline("compile_mps_shader('''")

        idx_vars = self.active_range_trees()
        with code.indent():
            if not V.graph.cpp_wrapper:
                for header in self.headers:
                    code.writeline(f"#include <c10/metal/{header}.h>")
            else:
                headers = [
                    f"#include <c10/metal/{header}.h>" for header in self.headers
                ]
                header_contents = _embed_headers(
                    headers,
                    [Path(__file__).parent.parent.parent / "include"],
                    OrderedSet(),  # type: ignore[arg-type]
                )
                code.writeline(header_contents)

            if self.inside_reduction:
                total_reduction_size = math.prod(
                    t.numel for t in self.range_trees if t.is_reduction
                )
                # If using dynamic shapes, set the threadgroup size to be the
                # max possible size
                threadgroup_size = (
                    min(total_reduction_size, self.max_threadgroup_size)
                    if isinstance(total_reduction_size, sympy.Integer)
                    else self.max_threadgroup_size
                )
                code.writeline(
                    f"[[max_total_threads_per_threadgroup({threadgroup_size})]]"
                )
            code.writeline(f"kernel void {fn_name}(")
            with code.indent():
                for outer, inner in self.args.output_buffers.items():
                    if outer in self.removed_buffers:
                        continue
                    dtype_str = self.dtype_to_str(V.graph.get_dtype(outer))
                    code.writeline(f"device {dtype_str}* {inner},")
                for outer, inner in self.args.input_buffers.items():
                    dtype = V.graph.get_dtype(outer)
                    # MPS does not support float64, but scalar inputs are fine
                    if dtype == torch.float64:
                        outer_buf = V.graph.try_get_buffer(outer)
                        if outer_buf is None or outer_buf.get_size() != []:
                            raise RuntimeError("float64 is not supported by MPS")
                        dtype_str = "float"
                    else:
                        dtype_str = self.dtype_to_str(dtype)
                    code.writeline(f"constant {dtype_str}* {inner},")
                for inner in self.args.sizevars.values():
                    code.writeline(f"constant long& {inner},")

                # Write dynamic values as inputs
                for idx_var in idx_vars:
                    if isinstance(idx_var.numel, sympy.Integer):
                        pass
                    else:
                        code.writeline(f"constant long& {idx_var.prefix}numel,")

                # Add error buffer parameter if error header is used
                if "error" in self.headers:
                    code.writeline("device c10::metal::ErrorMessages* error_buf,")

                assert len(idx_vars) < 4, "Up to 3 index variables are supported"
                thread_pos_dtype = (
                    f"uint{len(idx_vars)}" if len(idx_vars) > 1 else "uint"
                )
                thread_pos_var_name = (
                    idx_vars[0].name if len(idx_vars) == 1 else "thread_pos"
                )
                thread_pos_suffix = "," if self.inside_reduction else ""
                code.writeline(
                    f"{thread_pos_dtype} {thread_pos_var_name} [[thread_position_in_grid]]{thread_pos_suffix}"
                )
                if self.inside_reduction:
                    code.writeline(
                        f"{thread_pos_dtype} group_pos [[thread_position_in_threadgroup]]"
                    )
            code.writeline(") {")
            with code.indent():
                if len(idx_vars) > 1:
                    for idx, var in enumerate(idx_vars):
                        code.writeline(
                            f"auto {var.name} = thread_pos.{chr(120 + idx)};"
                        )
                code.splice(self.indexing_code)
                code.splice(self.body)
            code.writeline("}")

        if V.graph.cpp_wrapper:
            code.writeline(')MTL");')
        else:
            code.writeline("''')")

        return code.getvalue()