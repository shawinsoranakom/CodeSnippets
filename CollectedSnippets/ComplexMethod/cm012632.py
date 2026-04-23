def _write_wrapper_signature(
        self,
        prefix: IndentedBuffer,
        wrapper: CppWrapperGpu,
        arg_names: list[str],
        arg_types: list[Any] | None = None,
        signature: dict[str, str] | None = None,
    ) -> None:
        """Write the wrapper function signature including template and parameters."""
        if arg_types is None:
            arg_types = self.arg_types

        # Generate template types for tensor arguments
        template_types = [
            f"typename {name}_type_"
            for name, arg_type in zip(arg_names, arg_types)
            if isinstance(arg_type, (torch_dtype, UnwrapUnspecArg))
        ]
        if V.graph.aot_mode:
            template_types.append("typename kernels_type_")

        if template_types:
            prefix.writeline(f"template <{', '.join(template_types)}>")

        # Build parameter list
        param_lines = [
            self._get_cpp_param_type(name, arg_type, signature)
            for name, arg_type in zip(arg_names, arg_types)
        ]
        param_lines.append("int32_t device_idx_")
        param_lines.append(
            maybe_hipify_code_wrapper(
                f"{wrapper.device_codegen.cpp_stream_type()} stream_"
            )
        )
        if V.graph.aot_mode:
            param_lines.append("kernels_type_& kernels_")
        param_lines.append(
            "const std::optional<std::string>& cubin_dir_ = std::nullopt"
        )

        # Write function signature
        prefix.writeline(f"static __attribute__((noinline)) void {self.wrapper_name}(")
        with prefix.indent():
            for i, param in enumerate(param_lines):
                comma = "," if i < len(param_lines) - 1 else ""
                prefix.writeline(f"{param}{comma}")
        prefix.writeline("){")