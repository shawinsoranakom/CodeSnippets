def gen_vmap_plumbing(native_function: NativeFunction) -> str | None:
    schema = native_function.func
    sig = DispatcherSignature.from_schema(schema)
    returns = schema.returns

    # Only support cases where all returns are Tensors or vector<Tensor>
    if not accepts_at_least_one_tensor_input(schema):
        return None
    if len(returns) == 0:
        return gen_vmap_plumbing_no_returns(native_function)
    return_symint_overrides = [
        "_scaled_dot_product_flash_attention",
        "_scaled_dot_product_cudnn_attention",
        "_scaled_dot_product_flash_attention_quantized",
    ]
    if (
        not all(ret.type.is_tensor_like() for ret in returns)
        and schema.name.unambiguous_name() not in return_symint_overrides
    ):
        return None
    # in-place views need special handling
    if "inplace_view" in native_function.tags:
        return None

    if schema.kind() == SchemaKind.inplace:
        return gen_vmap_inplace_plumbing(native_function)

    # Don't support these (mutable, out, scratch)
    if schema.kind() != SchemaKind.functional:
        return None

    results_var = "results"
    cur_level_var = "cur_level"

    unwraps, unwrapped_arg_list = gen_unwraps(schema.arguments.flat_all, cur_level_var)
    bdims_all_none_case = gen_case_where_all_bdims_are_none(sig, schema, cur_level_var)

    wrapped_returns = gen_returns(returns, cur_level_var, results_var)
    return f"""\
template <typename batch_rule_t, batch_rule_t batch_rule>
{sig.decl(name=schema.name.unambiguous_name() + "_generated_plumbing")} {{
  c10::impl::ExcludeDispatchKeyGuard guard(DispatchKey::FuncTorchBatched);
  auto maybe_layer = maybeCurrentDynamicLayer();
  vmap_check_escaped(maybe_layer, "gen_vmap_plumbing");
  int64_t {cur_level_var} = maybe_layer->layerId();
{textwrap.indent(bdims_all_none_case, "  ")}
{textwrap.indent(unwraps, "  ")}
  auto {results_var} = batch_rule({", ".join(unwrapped_arg_list)});
  {wrapped_returns}
}}"""