def __exit__(
        self,
        type: Any,
        value: Any,
        traceback: Any,
    ) -> Literal[False]:
        # with block ended
        ctx = get_script_run_ctx()
        if ctx is not None:
            ctx.dg_stack.pop()

        # Re-raise any exceptions
        return False