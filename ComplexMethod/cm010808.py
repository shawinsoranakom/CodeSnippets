def call_and_expect_output_descs(
    fn: Callable[[*_Ts], tuple[Any, Any]], args: tuple[Unpack[_Ts]]
) -> tuple[Any, Any]:
    from .descriptors import AOTOutput

    outs_pair = fn(*args)
    if not (isinstance(outs_pair, tuple) and len(outs_pair) == 2):
        raise AssertionError(
            f"expected tuple of length 2, got {type(outs_pair)} with value {outs_pair}"
        )
    outs, outs_descs = outs_pair
    # The Tensor tests protects against the test when there are no outputs
    out_vals, out_spec = pytree.tree_flatten(outs)
    out_desc_vals, out_desc_spec = pytree.tree_flatten(outs_descs)
    if out_spec != out_desc_spec:
        raise AssertionError(
            f"output spec mismatch: {fn_wrappers(fn)}, outs={outs}, outs_descs={outs_descs}, "
            f"out_spec={out_spec}, out_desc_spec={out_desc_spec}"
        )
    if any(isinstance(x, AOTOutput) for x in out_vals):
        raise AssertionError(
            f"unexpected AOTOutput in out_vals: {fn_wrappers(fn)}, outs={outs}, "
            f"outs_descs={outs_descs}, out_vals={out_vals}"
        )
    if not all(
        isinstance(d, AOTOutput)
        for (x, d) in zip(out_vals, out_desc_vals)
        if isinstance(x, (torch.Tensor, torch.SymInt)) or type(x) is int
    ):
        raise AssertionError(
            f"expected all descriptors to be AOTOutput: {fn_wrappers(fn)}, outs={outs}, "
            f"outs_descs={outs_descs}, out_vals={out_vals}, out_desc_vals={out_desc_vals}"
        )
    return outs_pair