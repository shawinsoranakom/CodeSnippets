def inductor_fails(
    fx_g: torch.fx.GraphModule, args: Sequence[Any], check_str: str | None = None
) -> bool:
    has_cuda = False
    for arg in args:
        if isinstance(arg, torch.Tensor) and arg.is_cuda:
            has_cuda = True
            break

    def sync() -> None:
        if has_cuda:
            # Ensures that segfaults are surfaced
            torch.cuda.synchronize()

    from torch._inductor.compile_fx import compile_fx_inner

    try:
        result = fx_g(*args)
        assert isinstance(result, (tuple, list))
        assert not any(isinstance(x, (tuple, list)) for x in result)
    except Exception:
        return False

    sync()

    try:
        compile_args = _get_compile_args(fx_g, args)
        compile_mod = compile_fx_inner(fx_g, compile_args)
        assert not isinstance(compile_mod, str)
        compile_mod(args)
        sync()
    except Exception as e:
        if check_str is not None and check_str not in repr(e):
            return False
        print(repr(e))
        return True
    return False