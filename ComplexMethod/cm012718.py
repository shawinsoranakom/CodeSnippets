def _get_loop_body(fn_list):
    if all(isinstance(fn, LoopBody) for fn in fn_list):
        loop_bodies = fn_list
    else:
        if hasattr(fn_list[0], "original_fn"):
            # For the case of local buffer, we wrap the fn with localize_function
            assert all(hasattr(fn, "original_fn") for fn in fn_list)
            assert all(
                isinstance(fn.original_fn.args[0]._body, LoopBody) for fn in fn_list
            )
            loop_bodies = [fn.original_fn.args[0]._body for fn in fn_list]
        else:
            assert all(isinstance(fn, functools.partial) for fn in fn_list)
            assert all(isinstance(fn.args[0]._body, LoopBody) for fn in fn_list)
            loop_bodies = [fn.args[0]._body for fn in fn_list]
    assert loop_bodies is not None
    return loop_bodies