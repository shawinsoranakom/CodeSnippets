def aot_export_module(
    mod: nn.Module,
    args: Iterable[Any],
    *,
    decompositions: dict[OpOverload, Callable[..., Any]] | None = None,
    # If true, we'll return a joint forward-backward graph,
    # As well as metadata on the loss + gradients in the backward.
    trace_joint: bool,
    # If trace_joint is True, we expect your module to return a scalar loss.
    # Your module can return multiple outputs, so you must specify which output the loss is.
    output_loss_index: int | None = None,
    pre_dispatch: bool = False,
    # If None, will be inferred from inputs and mod.graph.nodes if mod is a graph module, but the inferred result might be wrong.
    dynamic_shapes: bool | None = None,
    kwargs: dict[str, Any] | None = None,
) -> tuple[Callable[..., Any] | torch.fx.GraphModule, GraphSignature]:
    """
    This function takes in a module, and returns:
    (1) an FX graph that can be exported
    (2) some metadata about the graph

    If `trace_joint=True` we will return a joint graph of the forward + backward.

    The traced FX graph will have the following properties compared to the original module:
    (1) Inputs and outputs to the module will be pytree-flattened
    (2) Parameters and buffers on the module will be lifted into graph inputs,
        graph_inputs = (*parameters, *buffers, *user_inputs)
    (3) The graph will be fully functionalized
    (4) Any input mutations will be converted into additional outputs in the graph,
        meaning whoever calls this graph is responsible for applying the mutations
        back to the original inputs.
    (5) If is_joint is provided the graph will return parameter gradients in addition to user outputs.
        The graph output will look like:
        graph_outputs = (*updated_inputs, *user_outputs, *param_gradients)

    There are also several restrictions on what modules can use this API. In particular:
    (1) If trace_joint is specified, we expect the loss function to be **fused**
        into the module forward. One of the outputs to the forward must be a scalar loss,
        which is specified with `output_loss_index`.
        All other outputs to the forward are presumed to not require gradients.
    (2) This API cannot capture optimizers (although in theory we could build an API for this).
    (3) Metadata mutations on params/buffers/inputs are banned.
    (4) Data mutations on anything that requires gradients are banned (parameters)
    (5) If an input is mutated, it is not allowed to alias any other inputs.
    (6) Parameters must not be duplicated.
    """
    if pre_dispatch and trace_joint:
        raise RuntimeError("pre_dispatch is not supported when trace_joint is True.")
    named_parameters = dict(mod.named_parameters(remove_duplicate=False))
    named_buffers = dict(mod.named_buffers(remove_duplicate=False))

    params_and_buffers = {
        **dict(named_parameters),
        **dict(named_buffers),
    }
    params_and_buffers_flat, params_spec = pytree.tree_flatten(params_and_buffers)
    params_and_buffers_flat = tuple(params_and_buffers_flat)
    params_len = len(params_and_buffers_flat)

    kwargs = kwargs or {}

    functional_call = create_functional_call(
        mod, params_spec, params_len, store_orig_mod=True
    )

    num_fw_outs = None

    if trace_joint:
        # This helper effectively just adds some extra asserts about what the backward will look like:
        # Outputs must include a scalar loss, that we compute gradients w.r.t.
        # We don't compute gradients w.r.t. anything else: so just in case we detach()
        # and other output tensors.
        def fn_to_trace(*args: Any) -> Any:
            nonlocal num_fw_outs
            out = functional_call(*args)
            if output_loss_index is None:
                raise RuntimeError(
                    """\
If trace_joint=Trueit is required that one of your forward outputs must be a scalar loss.
You must specify the which (index) output is the loss with output_loss_index."""
                )
            if isinstance(out, (torch.Tensor)):
                out = (out,)
            if not isinstance(out, (tuple, list)):
                raise RuntimeError(
                    f"Expected forward output to be either a tensor or a list/tuple of tensors. found {type(out)}"
                )

            for i, o in enumerate(out):
                # We only want to create a backward graph w.r.t. the loss that the user passed in.
                # This implies that every other output should not require gradients.
                # Instead of making this an error (and forcing the user to detach all other outputs
                # of their forward),
                # we'll automatically detach them here.
                if o.requires_grad and i != output_loss_index:
                    raise RuntimeError(
                        f"""\
Found an output of the forward that requires gradients, that was not the scalar loss.
We require all outputs to the forward that are not the scalar loss to not require gradient,
because we will only compute a backward graph against the scalar loss.
You can fix this by calling .detach() on each of your forward outputs that is not the loss.
You specified that output index {output_loss_index} is the loss, but we found that
the output at index {i} requires gradients."""
                    )
            out_loss = out[output_loss_index]
            num_fw_outs = len(out)
            if not out_loss.requires_grad:
                raise RuntimeError(
                    f"""\
The output at index {output_loss_index} was marked as the loss, but it does not require gradients"""
                )
            if out_loss.numel() != 1:
                raise RuntimeError(
                    f"""\
We require the output marked as the loss (at index {output_loss_index}) to be a scalar, but it has shape {out_loss.shape}"""
                )
            return out

        ctx = nullcontext
    else:
        # Run under no_grad, so our tracing machinery only traces an inference graph.
        # However if pre_dispatch=True, we want to correctly trace set_grad_enabled calls for training.
        ctx = nullcontext if pre_dispatch else torch.no_grad
        fn_to_trace = functional_call

    full_args = []
    # First, the params
    # NB: It is REQUIRED that parameters come first, Inductor infers "fixed"
    # parameters by looking at the difference in parameter count outside
    # and inside AOTAutograd, and assumes the prefix of arguments are fixed
    # arguments
    full_args.extend(params_and_buffers_flat)
    # Next, the input args
    full_args.extend(args)

    with ctx():
        fx_g, metadata, in_spec, out_spec = _aot_export_function(
            fn_to_trace,
            tuple(full_args),
            decompositions=decompositions,
            num_params_buffers=params_len,
            no_tangents=True,
            pre_dispatch=pre_dispatch,
            dynamic_shapes=dynamic_shapes,
            trace_joint=trace_joint,
            kwargs=kwargs,
        )

    # TODO: subsume this path with the aot_stage2_graph_capture path
    if trace_joint:

        @wraps(functional_call)
        def flattened_joint(*args: Any) -> Any:
            # The idea here is that the joint graph that AOTAutograd creates has some strict properties:
            # (1) It accepts two arguments (primals, tangents), and pytree_flattens them
            # (2) It returns a tuple of (fw_outs, gradients)
            # This is a very useful convention for anyone who wants to partition the joint graph
            # into a separate forward and backward graph.
            # However,
            # (1) for people exporting a single joint graph, it would be preferable not to have
            #     any pytrees in the graph.
            # (2) We are guaranteed in the aot_export_module case that the forward outputs a loss,
            #     and there are therefore no tangents that are needed to run the joint graph.
            # (3) AOTAutograd creates a grad_input for every input in the forward,
            #     including None's for inputs that are not grad-requiring tensors.
            #     we don't want these in our export graph.
            #     and there are therefore no tangents that are needed to run the joint graph.
            # This function "fixes" both of the above by removing any tangent inputs,
            # and removing pytrees from the original FX graph.
            fake_tangents = [
                None
                for _ in range(
                    metadata.num_outputs + metadata.num_mutated_inp_runtime_indices
                )
            ]
            fw_outs, gradients = fx_g(args, fake_tangents)
            if len(gradients) != len(args):
                raise AssertionError(
                    f"len(gradients)={len(gradients)} != len(args)={len(args)}"
                )
            output_gradients = []
            for a, grad in zip(args, gradients):
                if isinstance(a, torch.Tensor) and a.requires_grad:
                    if grad is None:
                        raise AssertionError("""\
Found a parameter that did not receive a gradient.
"This is most likely a bug, but if this needs to be supported please comment on this Github issue:
https://github.com/pytorch/pytorch/issues/101192
""")
                    output_gradients.append(grad)
                else:
                    if grad is not None:
                        raise AssertionError(
                            f"expected grad to be None for non-tensor or non-requires_grad input, got {type(grad)}"
                        )
            return *fw_outs, *output_gradients

        fx_g = make_fx(flattened_joint, record_module_stack=True)(*full_args)

    user_args_flat = pytree.arg_tree_leaves(*args, **kwargs)
    if out_spec is None:
        raise AssertionError("out_spec must not be None")
    return fx_g, create_graph_signature(
        # type: ignore[bad-argument-type]
        fx_g,
        metadata,
        in_spec,
        out_spec,
        user_args_flat=user_args_flat,
        params_and_buffers_flat=list(params_and_buffers_flat),
        param_names=list(named_parameters.keys()),
        buffer_names=list(named_buffers.keys()),
        trace_joint=trace_joint,
        num_user_fw_outs=num_fw_outs,
        loss_index=output_loss_index,
    )