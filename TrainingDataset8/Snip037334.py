def __enter__(self) -> None:
        # with block started
        ctx = get_script_run_ctx()
        if ctx:
            ctx.dg_stack.append(self)