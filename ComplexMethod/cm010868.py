def create_graph_signature(
    fx_g: torch.fx.GraphModule,
    fw_metadata: ViewAndMutationMeta,
    in_spec: pytree.TreeSpec,
    out_spec: pytree.TreeSpec,
    *,
    user_args_flat: list[Tensor],
    params_and_buffers_flat: list[Tensor],
    param_names: list[str],
    buffer_names: list[str],
    trace_joint: bool,
    num_user_fw_outs: int | None,
    loss_index: int | None,
) -> GraphSignature:
    # Retrieve graph input names
    graph_input_names = _graph_input_names(fx_g)
    # Retrieve graph output names
    graph_output_names = _graph_output_names(fx_g)

    num_params_buffers = len(param_names) + len(buffer_names)
    num_tokens = len(fw_metadata.tokens)
    # We have enough restrictions on the graph (no de-duping, synthetic bases, etc),
    # Such that # graph inps = # user inps + # params + # buffers
    num_user_args = len(graph_input_names) - num_params_buffers - num_tokens

    if trace_joint:
        if num_user_fw_outs is None:
            raise AssertionError(
                "num_user_fw_outs must not be None when trace_joint=True"
            )
        num_fw_outs = num_user_fw_outs + fw_metadata.num_mutated_inp_runtime_indices
        backward_output_names = graph_output_names[num_fw_outs:]

        grad_index = itertools.count(0)
        gradients_to_parameters = {
            backward_output_names[next(grad_index)]: param_names[i]
            for i, param in enumerate(params_and_buffers_flat)
            if param.requires_grad
        }

        gradients_to_user_inputs = {
            backward_output_names[next(grad_index)]: graph_input_names[
                i + len(params_and_buffers_flat)
            ]
            for i, user_input in enumerate(user_args_flat)
            if user_input.requires_grad
        }

        if len(gradients_to_parameters) + len(gradients_to_user_inputs) != len(
            backward_output_names
        ):
            raise AssertionError(
                f"len(gradients_to_parameters)={len(gradients_to_parameters)} + "
                f"len(gradients_to_user_inputs)={len(gradients_to_user_inputs)} != "
                f"len(backward_output_names)={len(backward_output_names)}"
            )

        # Check that we have fully accounted for all graph outputs
        if loss_index is None:
            raise AssertionError("loss_index must not be None")
        backward_signature = BackwardSignature(
            gradients_to_parameters,
            gradients_to_user_inputs,
            graph_output_names[loss_index],
        )
    else:
        backward_signature = None
        num_user_fw_outs = (
            len(graph_output_names)
            - fw_metadata.num_mutated_inp_runtime_indices
            - num_tokens
        )

    return GraphSignature.from_tracing_metadata(
        in_spec=in_spec,
        out_spec=out_spec,
        graph_input_names=graph_input_names,
        graph_output_names=graph_output_names,
        view_mutation_metadata=fw_metadata,
        named_parameters=param_names,
        named_buffers=buffer_names,
        num_user_inputs=num_user_args,
        num_user_outputs=num_user_fw_outs,
        trace_joint=trace_joint,
        loss_index=loss_index,
        backward_signature=backward_signature,
    )