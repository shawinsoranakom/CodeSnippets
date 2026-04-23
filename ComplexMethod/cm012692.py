def generate_c_shim_fallback_kernel(
        self, fallback_kernel: ir.FallbackKernel, args: list[str]
    ) -> None:
        output_args = []
        output_raii_handles = []
        output_name_base = fallback_kernel.get_name()
        for idx, output in enumerate(fallback_kernel.outputs):
            if isinstance(output, ir.MultiOutput):
                # TODO: handle integer output (e.g., as in attention)
                name = f"{output.get_name()}"
                output_handle_name = f"{name}_handle"
                if output.indices:
                    assert output.indices[0][1] == idx, (
                        f"expected {output.indices[0][1]=} == {idx=} for {output_name_base=}"
                    )
                self.writeline(f"AtenTensorHandle {output_handle_name};")
                output_args.append(f"&{output_handle_name}")
                output_raii_handles.append(
                    f"RAIIAtenTensorHandle {name}({output_handle_name});"
                )
            elif isinstance(output, int):
                output_name = f"{output_name_base}_{idx}"
                self.writeline(f"int64_t {output_name} = {output};")
                output_args.append(f"&{output_name}")
            elif isinstance(output, sympy.Expr):
                output_name = f"{output_name_base}_{idx}"
                self.writeline(f"auto {output_name} = {cexpr(output)};")
                output_args.append(f"&{output_name}")
            elif output is None:
                output_args.append("nullptr")
            else:
                raise NotImplementedError(f"unsupported type of {output=}")
        args = args + output_args
        device = d.type if (d := fallback_kernel.get_device()) else self.device

        self.generate_c_shim_extern_kernel_call(
            fallback_kernel.cpp_kernel_name,  # type: ignore[arg-type]
            args,
            device,
        )
        for raii_handle in output_raii_handles:
            self.writeline(raii_handle)