def create_aot_state(
    stack: contextlib.ExitStack,
    flat_fn: Callable[_P, _R],
    fake_flat_args: FakifiedFlatArgs,
    flat_args_descs: list[AOTInput],
    aot_config: AOTConfig,
    fake_mode: FakeTensorMode,
    shape_env: ShapeEnv | None,
) -> AOTState:
    """
    Traces the forward and backward graphs of the attr:`flat_fn` to generate a
    joint graph. The joint graph is an Fx graph with Aten ops. Please refer to
    the tracing mechanism to understand the graph capturing details.

    The joint graph is then passed through attr:`partition_fn` to isolate the
    forward and backward portions, which are then respectively compiled via the
    provided attr:`fw_compiler` and attr:`bw_compiler`.

    The resulting compiled forward and backward graphs are then wrapped up in a
    ``torch.autograd.Function`` object.

    The calling convention here is that the first aot_config.num_params_buffers
    inputs in flat_args are parameters and buffers, and the rest are inputs.

    We use this to assume that parameters/buffer's shapes don't change.
    """

    # Old name for now to avoid messing with stats.  Also, note this is pushed
    # on the stack, so it extends BEYOND this function
    stack.enter_context(
        dynamo_timed("create_aot_dispatcher_function", log_pt2_compile_event=True)
    )

    # This is the main entry point.
    # TODO: Chillee argues that dynamo itself should pass in fake tensors to
    # the list of arguments when compiling; at the moment we do not do this

    if aot_config.decompositions is None:
        aot_config.decompositions = {}

    aot_config.decompositions = {
        **aot_autograd_decompositions,
        **aot_config.decompositions,
    }

    if config.functionalize_rng_ops:
        # Update the decompositions with functionalized random decompositions
        aot_config.decompositions = {  # type: ignore[assignment]
            **rng_decompositions,
            **aot_config.decompositions,
        }

    # Check flat_args to see if they're already fake.  If so, use that fake
    # mode instead.

    python_dispatcher_mode = (
        enable_python_dispatcher() if shape_env is not None else nullcontext()
    )

    # See NOTE: [Deferring tensor pack/unpack hooks until runtime]
    # If any saved tensor hooks are active, we **don't** want to trace them.
    # Instead, we'll let them run at runtime, around the custom autograd.Function
    # that we generate in torch.compile.
    stack.enter_context(torch.autograd.set_multithreading_enabled(False))
    stack.enter_context(preserve_rng_state())
    stack.enter_context(fake_mode)
    stack.enter_context(python_dispatcher_mode)
    stack.enter_context(PhiloxStateTracker())
    stack.enter_context(
        torch._dynamo.utils._disable_saved_tensors_hooks_during_tracing()
    )

    from torch._library.fake_class_registry import FakeScriptObject, maybe_to_fake_obj
    from torch._library.opaque_object import is_opaque_type

    # Tracing may mutate the states the fake script object,
    # so we need to duplicate the fake script objects so that subsequent tracing
    # won't be affected.
    def _dup_fake_script_obj(fake_flat_args: FakifiedFlatArgs) -> list[Any]:
        return [
            maybe_to_fake_obj(detect_fake_mode(fake_flat_args), arg.real_obj)
            if isinstance(arg, FakeScriptObject) or is_opaque_type(type(arg))
            else arg
            for arg in fake_flat_args
        ]

    needs_autograd = any(
        x.requires_grad for x in fake_flat_args if isinstance(x, Tensor)
    )

    with enable_python_dispatcher():
        # Patch set_rng_state as set_rng_state with fake tensors is
        # nonsensical. This does not affect the collection of metadata.
        with patch("torch.cuda.set_rng_state", lambda *args: None):
            mod = root_module_when_exporting_non_strict(flat_fn)
            if mod is not None:
                ctx = _detect_attribute_assignment(mod)
            else:
                ctx = nullcontext()

            if torch._functorch.config.fake_tensor_propagate_real_tensors:
                # Running dynamo_timed causes fake tensor issues when
                # propagate real tensor is switched on.
                dynamo_timed_ctx = nullcontext()
            else:
                dynamo_timed_ctx = dynamo_timed(
                    "aot_collect_metadata", log_pt2_compile_event=True
                )

            with dynamo_timed_ctx, ctx:
                fw_metadata = run_functionalized_fw_and_collect_metadata(
                    flat_fn,
                    flat_args_descs=flat_args_descs,
                    static_input_indices=aot_config.static_input_indices,
                    keep_input_mutations=aot_config.keep_inference_input_mutations,
                    pre_dispatch=aot_config.pre_dispatch,
                )(*_dup_fake_script_obj(fake_flat_args))

            req_subclass_dispatch = requires_subclass_dispatch(
                fake_flat_args, fw_metadata
            )
            CompileEventLogger.try_add_pt2_compile(
                "backend_compile", requires_subclass_dispatch=req_subclass_dispatch
            )

            output_and_mutation_safe = not any(
                x.requires_grad
                # view-type operations preserve requires_grad even in no_grad.
                # Do not count aliases of inputs with requires_grad as reason to make a training graph,
                # as AOTAutograd will perform view-replay to regenerate the view outputs at runtime,
                # setting their grad_fn properly.
                and not (
                    x.output_type in (OutputType.alias_of_input, OutputType.is_input)
                    and x.base_idx is not None
                    and fw_metadata.input_info[x.base_idx].requires_grad
                )
                for x in fw_metadata.output_info
            ) and not any(
                x.requires_grad
                and x.mutates_data
                and not x.mutations_under_no_grad_or_inference_mode
                and not x.mutations_hidden_from_autograd
                for x in fw_metadata.input_info
            )

            if needs_autograd and output_and_mutation_safe:
                # We realized that none of the outputs require grad,
                # and none of the inputs that require grad are mutated.
                # so we actually have an inference graph.
                needs_autograd = False

    if fw_metadata.num_intermediate_bases > 0:
        if req_subclass_dispatch:
            raise AssertionError(f"""\
torch.compile is currently being used with tensor subclass inputs.
We are attempting to a compile a graph with two graph outputs
that alias one another, specifically output indices:

    {[i for i, x in enumerate(fw_metadata.output_info) if x.output_type == OutputType.alias_of_intermediate]}

ANY output aliasing (even for regular tensors) is currently unsupported if
there are any subclass outputs. If you run into this, please file a github
issue""")

    if aot_config.is_export:
        # aot_export: ban input metadata mutations for now to keep shared code paths simpler.
        # Keeping .resize_() in the graph will require some work
        # Allowing it but keeping the graph functional will require some calling convention changes.
        if len([x for x in fw_metadata.input_info if x.mutates_metadata]) != 0:
            raise RuntimeError(
                f"""\
Found an input that received a metadata mutation, through e.g. a call to `.resize_()` or `.transpose_()`.
This is currently banned in the aot_export workflow. If you need this functionality, please file a github issue.

fw_metadata={str(fw_metadata)}"""
            )
        # In export, banning data mutations on inputs that require grad for now.
        # This should be rare, and is tricky to get right. When we trace the backward,
        # we currently trace with autograd.grad instead of .backward(), which makes it difficult
        # to ensure that we run autograd all the way through the input **before** it saw the mutation.
        if (
            len(
                [
                    x
                    for x in fw_metadata.input_info
                    if x.requires_grad and x.mutates_data
                ]
            )
            != 0
            and aot_config.export_trace_joint
        ):
            raise RuntimeError(
                f"""\
Found a graph input that requires gradients, and received a mutation.
This is currently banned in the aot_export workflow. If you need this functionality, please file a github issue.

fw_metadata={str(fw_metadata)}"""
            )
        if req_subclass_dispatch:
            raise RuntimeError(
                """\
aot_export is not currently supported with traceable tensor subclass.
If you need this feature, please comment on <CREATE_ISSUE_LINK>"""
            )

        # Need to decide on a strategy for functionalized RNG: toggling via global config seems bad,
        # and turning it on will require a non-trivial calling convention change for any export runtime.
        if config.functionalize_rng_ops:
            raise RuntimeError(
                """\
Functionalized RNG is not currently supported in the aot_export workflow. Please file a github issue,
or otherwise set torch._functorch.config.functionalize_rng_ops = False."""
            )

    return AOTState(
        needs_autograd=needs_autograd,
        flat_args=_dup_fake_script_obj(fake_flat_args),
        flat_args_descs=flat_args_descs,
        fw_metadata=fw_metadata,
        # Packaging this just for later use
        aot_config=aot_config,
        stack=stack,
        fake_mode=fake_mode,
    )