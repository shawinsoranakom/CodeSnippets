def gen_class_ctor(self, k: SchemaKind, class_name: str, returns: int) -> str:
        if k is SchemaKind.functional:
            return ""
        elif k is SchemaKind.inplace:
            # TODO: Make sure out argument is guaranteed to be self
            return f"{class_name}(Tensor& self) : outputs_{{std::ref(self)}} {{}}"
        elif k is SchemaKind.out:
            out_args = ", ".join(f"Tensor& out{i}" for i in range(returns))
            out_refs = ", ".join(f"std::ref(out{i})" for i in range(returns))
            return f"{class_name}({out_args}) : outputs_{{ {out_refs} }} {{}}"
        elif k is SchemaKind.mutable or k is SchemaKind.scratch:
            raise AssertionError(
                f"{k} structured operators are currently not supported"
            )
        else:
            assert_never(k)