def __call__(self, f: NativeFunction) -> str:
        if not self.selector.is_root_operator(f"aten::{f.func.name}"):
            return ""
        # We unconditionally generate function wrappers,
        sig_group = CppSignatureGroup.from_native_function(f, method=False)

        sig = sig_group.most_faithful_signature()

        # escape double quote in schema, get rid of extra double quotes
        schema = cpp_string(str(sig.func))[1:-1]

        # arguments
        args = sig.arguments()
        connector = ",\n\t\t"
        args_code = []
        for arg in args:
            # Using method=False faithful C++ API, so we should not see SelfArgument/TensorOptionsArgument
            if not isinstance(arg.argument, Argument):
                raise AssertionError(f"Expected Argument, got {type(arg.argument)}")
            if not arg.argument.default:
                arg_cpp = "c10::IValue(::std::nullopt)"
            else:
                # The unboxing code uses the faithful C++ API to avoid the overhead
                # from wrapping/unwrapping TensorOptios.
                # However, we would look to include default args for schema parsing.
                # Default args only show up in the nonfaithful C++ API,
                arg_default = cpp.default_expr(
                    arg.argument.default, arg.argument.type, symint=False
                )
                if arg_default.startswith("{"):
                    arg_cpp = f"c10::IntArrayRef({arg_default})"
                else:
                    arg_cpp = f"c10::IValue({arg_default})"
            args_code.append(
                f"""c10::Argument("{arg.name}", nullptr, ::std::nullopt, {arg_cpp})"""
            )

        returns = f.func.returns
        returns_code = []
        for ret in returns:
            returns_code.append(f"""c10::Argument("{ret.name if ret.name else ""}")""")
        return f"""
// aten::{schema}
OperatorGenerator(
    "aten::{f.func.name.name}",
    "{f.func.name.overload_name}",
    {{
        {connector.join(args_code)}
    }},
    {{
        {connector.join(returns_code)}
    }},
    [](Stack & stack) {{
        RECORD_FUNCTION("{sig.name()}", std::vector<c10::IValue>());
        at::unboxing::{unboxing.name(f)}(stack);
    }},
    aliasAnalysisFromSchema()
),
"""