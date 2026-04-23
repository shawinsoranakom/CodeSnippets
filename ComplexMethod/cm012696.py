def generate_fallback_kernel_with_runtime_lookup_nopython(
        self,
        get_args: Callable[[], Sequence[str]],
        op_overload: torch._ops.OpOverload,
        output_args: Sequence[str | None],
        raw_outputs: Sequence[ir.Buffer],
    ) -> None:
        """Generate fallback kernel calls with runtime (non-AOT) dispatch.  This can
        only be called in cpp_wrapper mode, and assumes that the input is a non-None
        OpOverload.

        In the future, we may switch over to directly calling c10::Dispatcher if we need
        to support more datatypes."""
        if raw_outputs:
            declarations_before_scope = [
                f"RAIIAtenTensorHandle {output_arg};"
                for output_arg, raw_output_arg in zip(output_args, raw_outputs)  # type: ignore[arg-type]
                if output_arg is not None
                and not isinstance(raw_output_arg, ir.MutationOutput)
            ]
        else:
            declarations_before_scope = [
                f"RAIIAtenTensorHandle {output_arg};"
                for output_arg in output_args  # type: ignore[arg-type]
                if output_arg is not None
            ]

        dispatch_lines = IndentedBuffer()
        dispatch_lines.writelines(declarations_before_scope)
        dispatch_lines.writeline("{")

        with dispatch_lines.indent():
            tmp_var_number = count()

            def parse_arg(arg_type: torch.JitType, codegen_arg: str) -> str:
                # Strip off any temporary references; we're in an indented context, so
                # any saved-off variables will be auto-destroyed.
                new_codegen_arg = codegen_arg.removeprefix("&temporary_reference(")
                if new_codegen_arg != codegen_arg:
                    # If we removed temporary_reference, there's a good chance the
                    # variable ends with get() (which would retrieve an ATenTensorHandle
                    # from a temporary RAII handle).  Strip that off too, since we're
                    # going to save this in a temporary RAII handle.
                    if codegen_arg.endswith(".get())"):
                        codegen_arg = new_codegen_arg.removesuffix(".get())")
                    else:
                        codegen_arg = new_codegen_arg.removesuffix(")")

                if isinstance(arg_type, torch.OptionalType):
                    # If we have a pointer to a variable, strip it off and let
                    # from<std::optional> handle any internal pointers.
                    codegen_arg = codegen_arg.removeprefix("&")

                    if codegen_arg == "nullptr":
                        return "torch::stable::detail::from(std::nullopt)"

                    var_name = f"tmp_var_{next(tmp_var_number)}"
                    dispatch_lines.writeline(
                        f"std::optional {var_name}{{{parse_arg(arg_type.getElementType(), codegen_arg)}}};"
                    )
                    return f"torch::stable::detail::from({var_name})"

                raii_var = self.create_tmp_raii_handle_var_if_needed(
                    codegen_arg, dispatch_lines
                )
                temp_handle = raii_var != codegen_arg

                if isinstance(arg_type, torch.TensorType):
                    if not temp_handle:
                        # If the RAII tensor being referenced _isn't_ a temporary,
                        # scoped to this fallback call, then create a new handle
                        # referencing it which from<AtenTensorHandle> can steal.
                        var_name = f"tmp_var_{next(tmp_var_number)}"
                        dispatch_lines.writeline(f"AtenTensorHandle {var_name};")
                        dispatch_lines.writeline(
                            f"aoti_torch_new_tensor_handle({raii_var}, &{var_name});"
                        )
                        return f"torch::stable::detail::from({var_name})"
                    # If the RAII tensor _is_ a temporary scoped to this fallback call,
                    # simply release and steal the handle.
                    return f"torch::stable::detail::from({raii_var}.release())"
                return f"torch::stable::detail::from({codegen_arg})"

            codegen_args = get_args()
            ivalue_args = (
                parse_arg(a.type, c)
                for a, c in zip(op_overload._schema.arguments, codegen_args)
            )
            array_len = max(len(codegen_args), len(output_args))
            dispatch_lines.writeline(
                f"std::array<StableIValue, {array_len}> dispatch_vars{{{', '.join(ivalue_args)}}};"
            )
            dispatch_lines.writeline("AOTI_TORCH_ERROR_CODE_CHECK(")
            with dispatch_lines.indent():
                dispatch_lines.writeline(
                    f'aoti_torch_call_dispatcher("{op_overload._schema.name}", "{op_overload._schema.overload_name}", dispatch_vars.data())'
                )
            dispatch_lines.writeline(");")

            # assign result(s), ignoring None
            for idx, output_arg in enumerate(output_args):
                if output_arg is None:
                    continue
                dispatch_lines.writeline(
                    f"{output_arg} = torch::stable::detail::to<AtenTensorHandle>(dispatch_vars[{idx}]);"
                )

        dispatch_lines.writeline("}")
        self.writelines(dispatch_lines.getvalue().splitlines())