def gen_vmap_inplace_plumbing(native_function: NativeFunction) -> str | None:
    # Assumptions:
    # - only one argument is being modified in-place
    # - the argument that is being modified in-place is the first argument
    # - all returns are either Tensor, tuple of Tensor, or TensorList
    schema = native_function.func
    sig = DispatcherSignature.from_schema(schema)
    returns = schema.returns

    # Check assumptions. If these are invalid we return None
    # and punt the work to handle them to the future.
    if schema.kind() != SchemaKind.inplace:
        raise AssertionError(f"Expected inplace schema, got {schema.kind()}")
    if not is_mutated_arg(schema.arguments.flat_all[0]):
        return None
    if len([arg for arg in schema.arguments.flat_all if is_mutated_arg(arg)]) != 1:
        return None

    # Only support cases where all returns are Tensors or vector<Tensor>
    if len(returns) == 0:
        return None
    if not all(is_tensor(ret.type) or is_tensor_list(ret.type) for ret in returns):
        return None
    if not accepts_at_least_one_tensor_input(schema):
        return None

    cur_level_var = "cur_level"

    unwraps, unwrapped_arg_list = gen_unwraps(schema.arguments.flat_all, cur_level_var)
    bdims_all_none_case = gen_case_where_all_bdims_are_none(sig, schema, cur_level_var)

    return f"""\
template <typename batch_rule_t, batch_rule_t batch_rule>
{sig.decl(name=schema.name.unambiguous_name() + "_generated_plumbing")} {{
  c10::impl::ExcludeDispatchKeyGuard guard(DispatchKey::FuncTorchBatched);
  auto maybe_layer = maybeCurrentDynamicLayer();
  vmap_check_escaped(maybe_layer, "gen_vmap_inplace_plumbing");
  int64_t {cur_level_var} = maybe_layer->layerId();
{textwrap.indent(bdims_all_none_case, "  ")}
{textwrap.indent(unwraps, "  ")}
  batch_rule({", ".join(unwrapped_arg_list)});
  return {schema.arguments.flat_all[0].name};
}}"""