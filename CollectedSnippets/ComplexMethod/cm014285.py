def repro_run(options: Any, mod: nn.Module, load_args: Any) -> None:
    from torch._inductor.compile_fx import compile_fx_inner

    mod, args = repro_common(options, mod, load_args)

    from torch.cuda import synchronize

    compile_args = _get_compile_args(mod, args)
    compiled = compile_fx_inner(mod, compile_args)
    assert not isinstance(compiled, str)

    if options.accuracy != "":
        # We don't really respect --accuracy vs --strict-accuracy here, it
        # seems counterintuitive
        if not same_two_models(
            mod,
            compiled,  # type: ignore[arg-type]
            args,
            only_fwd=True,
            ignore_non_fp=config.repro_ignore_non_fp,
        ):
            raise AccuracyError("Bad accuracy detected")
    else:
        need_sync = False

        for arg in args:
            if isinstance(arg, torch.Tensor) and arg.is_cuda:
                need_sync = True
                break

        compiled(list(args))

        if need_sync:
            synchronize()