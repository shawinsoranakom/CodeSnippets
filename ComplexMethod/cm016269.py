def go(f: NativeFunction) -> str:
        # header comments
        if isinstance(ps, PythonSignatureDeprecated):
            schema_comment = f"// [deprecated] aten::{ps.deprecated_schema}"
        else:
            schema_comment = f"// aten::{f.func}"

        # dispatch lambda signature
        name = cpp.name(f.func)
        lambda_formals = ", ".join(
            f"{a.type_str} {a.name}" for a in dispatch_lambda_args(ps, f, symint=symint)
        )
        lambda_return = dispatch_lambda_return_str(f)

        # dispatch lambda body
        dispatch_callee = cpp_dispatch_target(f)
        dispatch_args = ", ".join(cpp_dispatch_exprs(f, python_signature=ps))

        # from arg parser outputs to dispatch lambda arguments
        parser_outputs = arg_parser_output_exprs(ps, f, symint=symint)
        lambda_arg_exprs = dispatch_lambda_exprs(ps, f, symint=symint)
        inits = "\n".join(lambda_arg_exprs.inits)
        lambda_args = ", ".join(lambda_arg_exprs.exprs)

        # scatter fields
        # TODO: Checking `ps.method and ('requires_grad' in parser_outputs)` is a hacky
        #       solution for enabling the 'requires_grad' argument for tensor methods
        #       new_full, new_empty, and new_zeros. A much better but more difficult to
        #       implement solution involves refactoring according to Ed's description here:
        #       https://github.com/pytorch/pytorch/issues/36455#issuecomment-614767589
        need_set_requires_grad = ps.tensor_options_args and (
            not has_tensor_options(f)
            or (ps.method and ("requires_grad" in parser_outputs))
        )
        set_requires_grad = (
            f".set_requires_grad({parser_outputs['requires_grad'].expr})"
            if need_set_requires_grad
            else ""
        )

        if lambda_return == "void":
            # Make in-place foreach return `self` at python-binding level.
            # ref: https://github.com/pytorch/pytorch/pull/118622#pullrequestreview-1904804954
            self_arg = f.func.arguments.self_arg
            return_stmt: str
            if (
                str(f.func.name).startswith("_foreach_")
                and f.func.kind() == SchemaKind.inplace
            ):
                # note(crcrpar): `_foreach_pow.ScalarAndTensor` does NOT have its in-place
                # variant and it unlikely to have it in the future. Thus it's safe to have the following check.
                if self_arg is None or not is_tensor_list_type(self_arg.argument.type):
                    raise AssertionError(
                        "Expected self_arg to be a tensor list type for inplace foreach"
                    )
                return_stmt = """PyObject* self_tensorlist = _r.args[0];
Py_INCREF(self_tensorlist);
return self_tensorlist;
"""
            else:
                return_stmt = "Py_RETURN_NONE;"
            return f"""\
{schema_comment}
{inits}
auto dispatch_{name} = []({lambda_formals}) -> {lambda_return} {{
  pybind11::gil_scoped_release no_gil;
  {dispatch_callee}({dispatch_args});
}};
dispatch_{name}({lambda_args}){set_requires_grad};
{return_stmt}
"""
        else:
            typename = structseq_typenames.get(gen_structseq_typename_key(f))
            structseq_typeref = f"{typename}, " if typename is not None else ""
            return f"""\
{schema_comment}
{inits}
auto dispatch_{name} = []({lambda_formals}) -> {lambda_return} {{
  pybind11::gil_scoped_release no_gil;
  return {dispatch_callee}({dispatch_args});
}};
return wrap({structseq_typeref}dispatch_{name}({lambda_args}){set_requires_grad});
"""