def dispatch_lambda_exprs(
    ps: PythonSignature, f: NativeFunction, *, symint: bool = True
) -> DispatchLambdaArgumentExprs:
    # This method is to bind 'arg_parser_outputs' and 'lambda_args' by producing
    # 'inits' and 'lambda_args_exprs' for each lambda argument using arg parser
    # outputs.
    arg_parser_outputs = arg_parser_output_exprs(ps, f, symint=symint)
    lambda_args = dispatch_lambda_args(ps, f, symint=symint)
    inits: list[str] = []
    lambda_args_exprs: dict[str, str] = {}

    has_toptions = has_tensor_options(f)

    # 1. special inits/unpacking to provide binding exprs for lambda arguments.
    for a in ps.arguments(skip_tensor_options=True):
        name = a.name
        arg_parser_expr = arg_parser_outputs[a.name].expr

        if has_toptions and name == "self":
            # TODO: why this needs to be special case?
            inits.extend(
                [
                    f"auto self = {arg_parser_expr};",
                ]
            )
            lambda_args_exprs[name] = name
        elif (
            isinstance(a, PythonOutArgument)
            and len(a.outputs) > 1
            and f.func.is_out_fn()
        ):
            inits.extend(
                [
                    f"auto out = {arg_parser_expr};",
                ]
            )
            for i, out_arg in enumerate(a.outputs):
                lambda_args_exprs[out_arg.name] = f"out[{i}]"
        elif str(a.type) == "Dimname[]?":
            # [old codegen]
            # TODO: make this part of something more general, or get rid of it.
            # optional<ArrayRef<T>> are special. The PythonArgParser returns an
            # optional<vector<T>>, which cannot be implicitly converted to
            # optional<ArrayRef<T>>. One needs to unwrap the optional and rewrap.
            inits.extend(
                [
                    f"auto __{name} = {arg_parser_expr};",
                    f"::std::optional<DimnameList> {name} = __{name} ? ::std::make_optional(DimnameList(__{name}.value())) : ::std::nullopt;",
                ]
            )
            lambda_args_exprs[name] = name
        else:
            # default case - directly using PythonArgParser output expr
            lambda_args_exprs[name] = arg_parser_expr

    # method's self is passed directly to python binding, rather than parsed
    if ps.method:
        lambda_args_exprs["self"] = "self"

    # 2. special packing/checking for TensorOptions.
    tensor_options_args_names = [a.name for a in ps.tensor_options_args]
    if has_toptions:
        if f.func.is_out_fn():
            raise RuntimeError(f"{f.func}: tensor options with output arg")
        for a in ps.tensor_options_args:
            if a.name not in TENSOR_OPTIONS_FIELDS:
                raise RuntimeError(
                    f"{f.func}: unrecognized tensor options field '{a.name}' in python binding arguments"
                )
            if str(a.type) != TENSOR_OPTIONS_FIELDS.get(a.name):
                raise RuntimeError(
                    f"{f.func}: unrecognized type '{str(a.type)}' for tensor options field '{a.name}'"
                )
        if not all(a in tensor_options_args_names for a in TENSOR_OPTIONS_FIELDS):
            raise RuntimeError(
                f"{f.func}: incomplete tensor options args: {tensor_options_args_names}"
            )

        inits.append(
            f"""\
const auto options = TensorOptions()
    .dtype({arg_parser_outputs["dtype"].expr})
    .device({arg_parser_outputs["device"].expr})
    .layout({arg_parser_outputs["layout"].expr})
    .requires_grad({arg_parser_outputs["requires_grad"].expr})
    .pinned_memory({arg_parser_outputs["pin_memory"].expr});
torch::utils::maybe_initialize_device(options);
"""
        )
        lambda_args_exprs["options"] = "options"

    # 3. special case - access scattered TensorOptions fields without packing
    # TODO: maybe move to the generator side as it's not related to binding.
    if not has_toptions and tensor_options_args_names:
        if "dtype" in tensor_options_args_names:
            # we're an output-arg variant, check these args against output tensor
            if not f.func.is_out_fn():
                raise RuntimeError(
                    f"{f.func}: dtype in tensor_options_args without output arg, {ps} {ps.arguments}"
                )
            if not all(a in tensor_options_args_names for a in ("layout", "device")):
                raise RuntimeError(
                    f"{f.func}: incomplete tensor options for output check"
                )

            inits.append(
                f"""\
check_out_type_matches({arg_parser_outputs["out"].expr}, {arg_parser_outputs["dtype"].expr},
                       {arg_parser_outputs["dtype"].is_none_expr}, {arg_parser_outputs["layout"].expr},
                       {arg_parser_outputs["device"].expr}, {arg_parser_outputs["device"].is_none_expr});
"""
            )
        # we'll set requires_grad on outgoing tensor
        if "requires_grad" not in tensor_options_args_names:
            raise RuntimeError(
                f'{f.func}: expected "requires_grad" in tensor_options_args absent, but found [{tensor_options_args_names}]'
            )

    return DispatchLambdaArgumentExprs(
        exprs=tuple(lambda_args_exprs[a.name] for a in lambda_args),
        inits=inits,
    )