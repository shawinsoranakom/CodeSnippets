def val_to_arg_str_for_prim_type(self, val, type_) -> str:
        # TODO: not using type_ as the first step of refactoring. Will update this later.
        if isinstance(val, bool):
            return "1" if val else "0"
        elif isinstance(val, int):
            # uint64_t is long on Linux, but long long on MacOS and Windows
            return f"{val}LL" if sys.platform in ["darwin", "win32"] else f"{val}L"
        elif isinstance(val, complex):
            return f"c10::complex<double>{{ {self.generate_float_value(val.real)}, {self.generate_float_value(val.imag)} }}"
        elif isinstance(val, str):
            return f'"{val}"'
        elif isinstance(
            val, (ir.Buffer, ir.ReinterpretView, ir.StorageBox, ir.TensorBox)
        ):
            return val.codegen_reference()
        elif isinstance(val, torch.device):
            return self.codegen_device(val)
        elif isinstance(val, torch.dtype):
            return self.codegen_dtype(val)
        elif isinstance(val, torch.layout):
            return self.codegen_layout(val)
        elif isinstance(val, torch.memory_format):
            return self.codegen_memory_format(val)
        elif isinstance(val, float):
            return self.generate_float_value(val)
        elif isinstance(val, (list, tuple)):
            # FIXME: This happens because type_ is not always properly set to torch.ListType
            return f"{{{', '.join(self.val_to_arg_str(x, None) for x in val)}}}"
        elif isinstance(val, SymTypes):
            return cexpr(val.node.expr)
        elif isinstance(val, sympy.Expr):
            return cexpr(val)
        else:
            return repr(val)