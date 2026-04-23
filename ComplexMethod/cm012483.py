def val_to_arg_str(self, s, type_=None):
        from torch.utils._triton import has_triton_package

        if has_triton_package():
            import triton

        if isinstance(s, SymTypes):
            return pexpr(s.node.expr)
        elif isinstance(s, sympy.Expr):
            return pexpr(s)
        elif isinstance(s, (tuple, list)):

            @dataclasses.dataclass
            class Shim:
                ref: Any

                def __repr__(self):
                    return self.ref

            # Explicitly call the Python version of val_to_arg_str
            return repr(
                type(s)(Shim(PythonWrapperCodegen.val_to_arg_str(self, a)) for a in s)
            )
        elif isinstance(s, torch._ops.OpOverload):
            return _get_qualified_name(s)
        elif isinstance(s, (ir.Buffer, ir.MutableBox, ReinterpretView)):
            return s.codegen_reference()
        elif has_triton_package() and isinstance(s, triton.language.dtype):  # type: ignore[possibly-undefined]
            return repr(s)
        elif isinstance(s, (ir.GeneratorState, ir.OpaqueObjectState)):
            return s.codegen_reference()
        elif is_opaque_value_type(type(s)):
            obj_repr, opaque_types = get_opaque_obj_repr(s)
            for n, t in opaque_types.items():
                V.graph.opaque_value_type_classes[n] = t
            return obj_repr
        else:
            return repr(s)