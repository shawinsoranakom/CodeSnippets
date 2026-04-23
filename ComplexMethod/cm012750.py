def _get_arg_from_node(
        arg_ty: type,
        node: Buffer,
        size_hint_fn: Callable[[Expr | int], int],
        arg_renames: EVTArgRenames,
    ) -> str:
        from ..template import CUTLASSTemplate

        # Today, arguments are either a pointer to the
        # node's memory, a stride tuple, the datatype
        # Once again, need to check for local class type for stride tuple
        if (
            str(arg_ty)
            == "<class 'cutlass_cppgen.backend.c_types.tuple_factory_.<locals>.TupleType'>"
        ):
            DEFAULT_STRIDE_LEN = 3
            assert len(node.get_layout().stride) <= DEFAULT_STRIDE_LEN
            stride = [size_hint_fn(x) for x in node.get_layout().stride]
            for _ in range(DEFAULT_STRIDE_LEN - len(stride)):
                stride.append(0)

            def render_stride(x: int) -> str:
                # Handle EBO for 0 and 1
                if x == 0:
                    return "_0{}"
                elif x == 1:
                    return "_1{}"
                else:
                    return str(x)

            return f"{{{', '.join([render_stride(x) for x in stride])}}}"

        elif issubclass(arg_ty, ctypes.c_void_p):
            name = arg_renames.new_name(node.get_name())
            return f"({CUTLASSTemplate._DTYPE_TO_CUTLASS[node.get_layout().dtype]}*) ({name} + {name}_offset)"
        elif (
            arg_ty in _CUTLASS_C_DTYPES
        ):  # Assumption: this is the element dtype, this holds for all cutlass ir nodes currently
            return f"{CUTLASSTemplate._DTYPE_TO_CUTLASS[node.get_layout().dtype]}(0)"
        elif issubclass(arg_ty, EmptyByte):
            return "{}"

        raise NotImplementedError(f"Unsupported arg type: {arg_ty}")