def gen_out_inplace_wrapper(
        self, f: NativeFunction, g: NativeFunctionsGroup | None
    ) -> str | None:
        if g is None:
            return None
        k = f.func.kind()
        if k is SchemaKind.inplace:
            copy_op = "at::_copy_from"
        elif k is SchemaKind.out:
            copy_op = "at::_copy_from_and_resize"
        else:
            raise AssertionError("gen_out_inplace_wrapper called on a functional op")

        sig = self.wrapper_kernel_sig(f)
        name = sig.name()

        func_res = f"{name}_tmp"
        return_names = cpp.return_names(f)
        if len(return_names) > 1:
            updates = "\n  ".join(
                f"{copy_op}(std::get<{i}>({func_res}), {ret_name});"
                for i, ret_name in enumerate(return_names)
            )
            returns = f"{sig.returns_type().cpp_type()}({', '.join(return_names)})"
        elif len(return_names) == 1:
            ret_name = return_names[0]
            updates = f"{copy_op}({func_res}, {ret_name});"
            returns = ret_name
        else:
            if len(f.func.arguments.out) != 1:
                raise AssertionError(
                    f"Expected exactly 1 out argument, got {len(f.func.arguments.out)}"
                )
            returns = ""
            out_arg = f.func.arguments.out[0]
            if out_arg.type.is_list_like():
                updates = f"""\
    for (int64_t i = 0; i < {func_res}.size(); ++i) {{
        {copy_op}({func_res}[i], {out_arg.name}[i]);
    }}"""
            else:
                updates = f"{copy_op}({func_res}, {out_arg.name});"

        functional_sig = self.wrapper_kernel_sig(g.functional)
        wrapper_name = sig.name()

        return f"""\
{sig.defn(name=wrapper_name)} {{
  auto {func_res} = {functional_sig.name()}({", ".join(e.expr for e in translate(sig.arguments(), functional_sig.arguments()))});
  {updates}
  return {returns};
}}
"""