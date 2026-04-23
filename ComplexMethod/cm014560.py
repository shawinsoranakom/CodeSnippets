def gen_returns(schema: FunctionSchema) -> tuple[list[str], list[str]]:
    types = []
    names = []
    for idx, ret in enumerate(schema.returns):
        names.append(f"ret{idx}")
        if isinstance(ret.type, BaseType) and ret.type.name in base_type_to_c_type:
            types.append(base_type_to_c_type[ret.type.name] + "*")
        else:
            raise NotImplementedError(
                f"TODO: add support for return type {repr(ret.type)}"
            )

    def convert_return(typ: BaseType, val: str) -> str:
        if typ.name == BaseTy.Tensor:
            return f"new_tensor_handle(std::move({val}))"
        elif typ.name == BaseTy.SymInt:
            return f"{val}.expect_int()"
        elif typ.name == BaseTy.Scalar:
            return f"{val}.toDouble()"
        else:
            return val

    ret_pointer_can_be_null = False
    unambiguous_name = schema.name.unambiguous_name()
    for name in (
        "_functional_sym_constrain_range",
        "_scaled_dot_product_cudnn_attention",
        "_scaled_dot_product_efficient_attention_backward",
        "_scaled_dot_product_efficient_attention",
        "_scaled_dot_product_flash_attention",
        "_scaled_dot_product_fused_attention_overrideable",
        "_thhn_fused_lstm_cell_backward_impl",
        "convolution_backward",
        "grid_sampler_2d_backward",
        "grid_sampler_3d_backward",
        "linear_backward",
    ):
        if name in unambiguous_name:
            ret_pointer_can_be_null = True
            break

    callsite_exprs: list[str] = []
    for idx, ret in enumerate(schema.returns):
        tmp = "tmp_result" if len(names) == 1 else f"std::get<{idx}>(tmp_result)"
        if not isinstance(ret.type, BaseType):
            raise AssertionError(f"Expected BaseType for return, got {type(ret.type)}")
        rval = convert_return(ret.type, tmp)
        if ret_pointer_can_be_null:
            callsite_exprs.append(f"if ({names[idx]}) {{ *{names[idx]} = {rval}; }}")
        else:
            callsite_exprs.append(f"*{names[idx]} = {rval};")

    return zip_type_and_name(types, names), callsite_exprs