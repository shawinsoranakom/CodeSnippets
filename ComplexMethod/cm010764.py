def aot_export_joint_simple(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    *,
    trace_joint: bool,
    # It looks like the main consequence of this API is that for dynamic shapes,
    # it will assume that params/buffers are static.
    # With the new inferred dynamic shapes API, maybe this doesn't matter?
    num_params_buffers: int = 0,
    decompositions: dict[OpOverload, Callable[..., Any]] | None = None,
) -> Callable[..., Any]:
    """
    A simplified version of export. Used by higher order operators.

    This function makes a high-level "no calling convention changes" guarantee:
    - If no inputs require grad (so we export an inference graph),
      there are *no* calling convention change between the exported graph, and "func".
    - If at least one input requires grad (so we trace out and export a joint fw-bw graph),
      Then if you were partition the graph into a separate forward and backward graph,
      The forward graph will have no calling convention changes compared to "func".

    The above also relies on some strong restrictions around which functions this API accepts:
    (1) `args` cannot contain any pytrees (they must have been pytree_flattened already)
    (2) `func` cannot mutate any inputs
    (3) The outputs of `func` cannot alias any inputs.

    Note: this function is only lightly tested today. It will probably be tested more heavily by higher order ops.
    """
    if trace_joint:
        ctx = nullcontext
    else:
        # Run under no_grad, so our tracing machinery only traces an inference graph.
        ctx = torch.no_grad

    with ctx():
        fx_g, metadata, in_spec, out_spec = _aot_export_function(
            func,
            args,
            decompositions=decompositions,
            trace_joint=trace_joint,
        )
        in_spec, _kw_in_spec = in_spec.children()
    # At this point, we can just directly return the (joint or inference graph) that we traced.
    # First though: a bunch of assertions to make sure that our graph doesn't require
    # any calling convention changes compared to the original function.
    # These restrictions are *in addition to* the general restrictions on export.

    # No input mutations
    if (
        len([x for x in metadata.input_info if x.mutates_data or x.mutates_metadata])
        != 0
    ):
        raise RuntimeError(
            f"aot_export_joint_simple does not support input mutations. {str(metadata)}"
        )
    # No output aliasing
    if (
        len([x for x in metadata.output_info if x.output_type != OutputType.non_alias])
        != 0
    ):
        raise RuntimeError(
            f"aot_export_joint_simple does not support outputs that alias inputs. {str(metadata)}"
        )
    # No pytrees
    if in_spec.is_leaf():
        raise RuntimeError(
            f"aot_export_joint_simple requires inputs to be a single list/tuple. in_spec={str(in_spec)}"
        )
    if not all(child.is_leaf() for child in in_spec.children()):
        raise RuntimeError(
            f"aot_export_joint_simple requires individual inputs not to be pytrees. in_spec={str(in_spec)}"
        )

    if out_spec is None:
        raise AssertionError("out_spec must not be None")
    if out_spec.is_leaf():
        raise RuntimeError(
            f"aot_export_joint_simple requires outputs to be a single list/tuple. out_spec={str(out_spec)}"
        )
    if not all(child.is_leaf() for child in out_spec.children()):
        raise RuntimeError(
            f"aot_export_joint_simple requires individual outputs not to be pytrees. out_spec={str(out_spec)}"
        )
    # TODO: we might have to temporarily patch config.functionalize_rng
    # so that it doesn't run when we're exporting a higher order op.

    if config.debug_assert:
        # Smoke test that after partitioning, we can run the forward without any calling convention changes.
        fw_module, _bw_module = default_partition(
            # type: ignore[bad-argument-type]
            fx_g,
            args,
            # type: ignore[unknown-name]
            num_fwd_outputs=len(fw_metadata.output_infos),  # noqa: F821
        )
        # Attempt to run the fw_module with the original user inputs
        fake_mode = detect_fake_mode(args)
        if fake_mode is None:
            fake_mode = FakeTensorMode()
        with fake_mode:
            fw_module(*args)
    return fx_g