def cpp_argdefs(
        self, dtype_to_cpp_type: dict[torch.dtype, str] | None = None
    ) -> tuple[list[str], list[str], list[str]]:
        from .cpp_utils import INDEX_TYPE

        if dtype_to_cpp_type is None:
            from .cpp_utils import DTYPE_TO_CPP

            dtype_to_cpp_type = DTYPE_TO_CPP

        call_args = []
        arg_defs = []
        arg_types = []
        for inplaced in unique(self.inplace_buffers.values()):
            if isinstance(inplaced, RemovedArg):
                continue
            outer = inplaced.other_names[-1]
            inner = inplaced.inner_name
            dtype = V.graph.get_dtype(outer)
            cpp_dtype = dtype_to_cpp_type[dtype]
            arg_defs.append(f"{cpp_dtype}* {inner}")
            call_args.append(self.wrap_ptr_arg(outer, dtype))
            arg_types.append(f"{cpp_dtype}*")
        for outer, inner in self.input_buffers.items():
            if outer in self.inplace_buffers:
                continue
            dtype = V.graph.get_dtype(outer)
            cpp_dtype = dtype_to_cpp_type[dtype]
            arg_defs.append(f"const {cpp_dtype}* {inner}")
            call_args.append(self.wrap_ptr_arg(outer, dtype))
            arg_types.append(f"const {cpp_dtype}*")
        for outer, maybe_inner in self.output_buffers.items():
            if outer in self.inplace_buffers or isinstance(maybe_inner, RemovedArg):
                continue
            dtype = V.graph.get_dtype(outer)
            cpp_dtype = dtype_to_cpp_type[dtype]
            arg_defs.append(f"{cpp_dtype}* {maybe_inner}")
            call_args.append(self.wrap_ptr_arg(outer, dtype))
            arg_types.append(f"{cpp_dtype}*")
        for outer, inner in self.sizevars.items():
            if isinstance(outer, sympy.Symbol) and symbol_is_type(
                outer, (SymT.UNBACKED_FLOAT)
            ):
                arg_defs.append(f"const float {inner}")
                arg_types.append("const float")
            else:
                arg_defs.append(f"const {INDEX_TYPE} {inner}")
                arg_types.append(f"const {INDEX_TYPE}")
            call_args.append(self.wrap_size_arg(outer))
            if V.graph.wrapper_code:
                V.graph.wrapper_code.ensure_size_computed(outer)
        assert not self.workspace_args, "Workspace not supported on CPU "
        return arg_defs, call_args, arg_types