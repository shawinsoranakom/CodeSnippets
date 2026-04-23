def _create_graph(
    f: Callable[..., Any],
    args: list[torch.Tensor],
    args_descs: list[AOTInput]
    | None = None,  # keep compat with old clients; maybe we should split into two impls
    *,
    aot_config: AOTConfig,
) -> torch.fx.GraphModule:
    # FunctionalTensorMode must be enabled here.
    # See Note [Accessing .grad_fn on FunctionalTensor]
    out_descs = None

    if args_descs is None:
        inner_f = f
    else:

        @simple_wraps(f)
        def inner_f(*args: Any) -> Any:
            nonlocal out_descs
            if out_descs is not None:
                raise AssertionError("out_descs must be None")
            out, out_descs = call_and_expect_output_descs(f, args)
            return out

    if aot_config.disable_functionalization:
        ctx = contextlib.nullcontext()
    else:
        ctx = FunctionalTensorMode(  # type: ignore[assignment]
            pre_dispatch=aot_config.pre_dispatch,
            export=aot_config.is_export,
            # Allow token discovery for joint fn tracing as tokens can be used in backward.
            _allow_token_discovery=True,
        )

    with (
        enable_python_dispatcher(),
        ctx,
    ):
        fx_g = make_fx(
            inner_f,
            decomposition_table=aot_config.decompositions,
            record_module_stack=True,
            pre_dispatch=aot_config.pre_dispatch,
            _disable_torch_fn_metadata_mode=aot_config._disable_torch_fn_metadata_mode,
        )(*args)

        if args_descs is not None:
            flat_args_descs, _ = pytree.tree_flatten(args_descs)
            flat_out_descs, _ = pytree.tree_flatten(out_descs)

            # Unfortunately, flat_args_descs is not guaranteed to match the
            # number of actual arguments that show up on the FX graph.
            # Specifically, allow_token_discovery=True means that we will
            # silently add extra token arguments to the backwards graph.
            #
            # Although there are a few ways to detect what these tokens are,
            # we are going to settle for something dodgy but simple to
            # implement: match tangents_token placeholders specifically,
            # as these are the only placeholders that are created by token
            # discovery (NB: there is NO other code that treats this name
            # as load bearing, so this is a bit naughty!)
            #
            # I originally wanted to detect tokens in exactly the same way
            # that they are detected at normal runtime, but to be honest
            # the normal runtime detection is pretty strange: it seems the
            # backward tokens are not reliably at the end of the argument list
            # but *precede* the RNG arguments (I don't understand why this is
            # the case).  And in unlift_tokens, token arguments are detected
            # by seeing if they feed into an effects call!  Dastardly.  Why
            # didn't we just introduce a new type.

            i = 0
            j = 0
            for n in fx_g.graph.nodes:
                if n.op == "placeholder":
                    if n.name.startswith("tangents_token"):
                        n.meta["desc"] = BackwardTokenAOTInput(j)
                        j += 1
                    else:
                        if i >= len(flat_args_descs):
                            raise AssertionError(
                                f"i={i} >= len(flat_args_descs)={len(flat_args_descs)}: "
                                f"fn_wrappers={fn_wrappers(inner_f)}, "
                                f"placeholders={[n for n in fx_g.graph.nodes if n.op == 'placeholder']}"
                            )
                        n.meta["desc"] = flat_args_descs[i]
                        i += 1
                elif n.op == "output":
                    n.meta["desc"] = flat_out_descs

    return fx_g