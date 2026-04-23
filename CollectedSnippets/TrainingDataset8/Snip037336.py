def _active_dg(self) -> "DeltaGenerator":
        """Return the DeltaGenerator that's currently 'active'.
        If we are the main DeltaGenerator, and are inside a `with` block that
        creates a container, our active_dg is that container. Otherwise,
        our active_dg is self.
        """
        if self == self._main_dg:
            # We're being invoked via an `st.foo` pattern - use the current
            # `with` dg (aka the top of the stack).
            ctx = get_script_run_ctx()
            if ctx and len(ctx.dg_stack) > 0:
                return ctx.dg_stack[-1]

        # We're being invoked via an `st.sidebar.foo` pattern - ignore the
        # current `with` dg.
        return self