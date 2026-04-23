def __call__(self, f: NativeFunction) -> str | None:
        if Variant.method not in f.variants:
            return None

        if f.func.is_out_fn():
            raise AssertionError(f"Method variant cannot be an out function: {f.func}")
        if f.func.arguments.self_arg is None:
            raise AssertionError(f"Method variant must have self_arg: {f.func}")

        sig_group = CppSignatureGroup.from_native_function(
            f, method=True, fallback_binding=f.manual_cpp_binding
        )

        if self.target is Target.DECLARATION:
            result = ""
            for sig in sig_group.signatures():
                result += f"{sig.decl()} const;\n"
            return result

        if self.target is not Target.DEFINITION:
            assert_never(self.target)

        result = ""

        for sig in sig_group.signatures():
            target_sig = DispatcherSignature.from_schema(f.func)
            exprs = translate(sig.arguments(), target_sig.arguments(), method=True)
            exprs_str = ", ".join([e.expr for e in exprs])

            result += f"""
// aten::{f.func}
inline {sig.defn(prefix="Tensor::")} const {{
    return at::_ops::{f.func.name.unambiguous_name()}::call({exprs_str});
}}
"""

        return result