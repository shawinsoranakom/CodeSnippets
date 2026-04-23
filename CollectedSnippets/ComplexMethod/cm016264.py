def load_deprecated_signatures(
    pairs: Sequence[PythonSignatureNativeFunctionPair],
    deprecated_yaml_path: str,
    *,
    method: bool,
    pyi: bool,
) -> list[PythonSignatureNativeFunctionPair]:
    # The deprecated.yaml doesn't have complete type information, we need
    # find and leverage the original ATen signature (to which it delegates
    # the call) to generate the full python signature.
    # We join the deprecated and the original signatures using type-only form.

    # group the original ATen signatures by name
    grouped: dict[str, list[PythonSignatureNativeFunctionPair]] = defaultdict(list)
    for pair in pairs:
        grouped[pair.signature.name].append(pair)

    # find matching original signatures for each deprecated signature
    results: list[PythonSignatureNativeFunctionPair] = []

    with open(deprecated_yaml_path) as f:
        deprecated_defs = yaml.load(f, Loader=YamlLoader)

    for deprecated in deprecated_defs:
        schema = FunctionSchema.parse(deprecated["name"])
        aten_name, call_args = split_name_params(deprecated["aten"])
        is_out = aten_name.endswith("_out")
        if is_out:
            aten_name = aten_name.replace("_out", "")

        # HACK: these are fixed constants used to pass the aten function.
        # The type must be known ahead of time
        known_constants = {
            "1": Type.parse("Scalar"),
        }
        schema_args_by_name = {a.name: a for a in schema.arguments.flat_all}
        for name in call_args:
            if name not in schema_args_by_name and name not in known_constants:
                raise AssertionError(
                    f"deprecation definition: Unrecognized value {name}"
                )

        # Map deprecated signature arguments to their aten signature and test
        # if the types and alias annotation match.
        def is_schema_compatible(
            aten_schema: FunctionSchema,
        ) -> bool:
            arguments: Iterable[Argument]
            if is_out:
                arguments = itertools.chain(
                    aten_schema.arguments.out, aten_schema.arguments.flat_non_out
                )
            else:
                arguments = aten_schema.arguments.flat_all

            for i, arg in enumerate(arguments):
                if i < len(call_args):
                    arg_name = call_args[i]
                    if arg_name in known_constants:
                        schema_type = known_constants[arg_name]
                        schema_annotation = None
                    else:
                        schema_arg = schema_args_by_name[arg_name]
                        schema_type = schema_arg.type
                        schema_annotation = schema_arg.annotation

                    if schema_type != arg.type or schema_annotation != arg.annotation:
                        return False
                else:
                    if arg.default is None:
                        return False

            return len(schema.returns) == len(aten_schema.returns) and all(
                a == b for a, b in zip(schema.returns, aten_schema.returns)
            )

        any_schema_found = False
        for pair in grouped[aten_name]:
            if not is_schema_compatible(pair.function.func):
                continue
            any_schema_found = True

            python_sig = signature_from_schema(
                schema,
                category_override=pair.function.category_override,
                method=method,
                pyi=pyi,
            )

            results.append(
                PythonSignatureNativeFunctionPair(
                    signature=PythonSignatureDeprecated(
                        name=python_sig.name,
                        input_args=python_sig.input_args,
                        input_kwargs=python_sig.input_kwargs,
                        output_args=python_sig.output_args,
                        tensor_options_args=python_sig.tensor_options_args,
                        method=python_sig.method,
                        deprecated_schema=schema,
                        deprecated_args_exprs=tuple(call_args),
                        returns=python_sig.returns,
                    ),
                    function=pair.function,
                )
            )
        if not any_schema_found:
            raise AssertionError(
                f"No native function with name {aten_name} matched signature:\n  {str(schema)}"
            )

    return results