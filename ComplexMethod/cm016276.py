def emit_view_body(
    fn: NativeFunctionWithDifferentiabilityInfo, var: str
) -> tuple[str, str]:
    # See NOTE [ Autograd View Variables ] in variable.h for details.
    f = fn.func
    base_name = get_base_name(f)
    view_info = get_view_info(f)
    call = ""
    differentiable_outputs = gen_differentiable_outputs(fn)
    differentiable_output_vars = {r.name for r in differentiable_outputs}
    if not isinstance(view_info, str):
        raise TypeError(
            f"The view info should be a string for {base_name}, but it is: {view_info}"
        )
    if len(differentiable_output_vars) == 0:
        # no output is differentiable (.indices() for SparseTensors for example)
        rhs_value = (
            f"as_view({view_info}, {var}, "
            f"/* is_bw_differentiable */ false, /* is_fw_differentiable */ false)"
        )
    elif len(differentiable_output_vars) == 1:
        # Single differentiable output (Tensor or Tensor[])
        return_info = differentiable_outputs[0]
        # We only support simple Tensor or a TensorList for functions that return views
        if not is_tensor_type(return_info.type) and not is_tensor_list_type(
            return_info.type
        ):
            raise RuntimeError(
                f"{base_name} that return differentiable views can only return Tensor or Tensor[]"
            )

        # See Note [ View + Inplace detection]
        def get_creation_meta_in_mode(original: str) -> str:
            creation_meta_with_grad_mode = f"(at::GradMode::is_enabled() ? {original} : CreationMeta::NO_GRAD_MODE)"
            return f"InferenceMode::is_enabled() ? CreationMeta::INFERENCE_MODE : {creation_meta_with_grad_mode}"

        # Only allow rebasing of the history if we return a single Tensor
        # If we are in a no grad block, raise a warning
        # See NOTE [ View + Inplace detection ] for more details about this logic
        if is_tensor_list_type(return_info.type):
            creation_meta = get_creation_meta_in_mode("CreationMeta::MULTI_OUTPUT_NODE")
            view_idx = "view_idx"
            view_func = emit_view_func(
                f, extract_bindings(f), view_idx=view_idx
            ).strip()
            as_view_call = (
                f"as_view(/* base */ {view_info}, /* output */ {var}[{view_idx}], "
                "/* is_bw_differentiable */ true, /* is_fw_differentiable */ true, "
                "/* view_func */ std::move(func), /* rev_view_func */ rev_func, "
                f"/* creation_meta */ {creation_meta});"
            )
            call += MULTI_OUTPUT_VIEW_ITERATION.substitute(
                var=var, view_idx=view_idx, body=f"{view_func}\n{as_view_call}"
            )
            rhs_value = f"std::move({var})"
        else:
            call += emit_view_func(f, extract_bindings(f), view_idx=None)
            creation_meta = get_creation_meta_in_mode("CreationMeta::DEFAULT")
            rhs_value = (
                f"as_view(/* base */ {view_info}, /* output */ {var}, /* is_bw_differentiable */ true, "
                "/* is_fw_differentiable */ true, "
                f"/* view_func */ std::move(func), /* rev_view_func */ rev_func, /* creation_meta */ {creation_meta})"
            )
    else:
        # This could be supported but we don't need it at the moment, so keeping things simple.
        raise RuntimeError(
            "Function that return multiple differentiable output "
            "when at least one of them is view is not supported."
        )
    return call, rhs_value