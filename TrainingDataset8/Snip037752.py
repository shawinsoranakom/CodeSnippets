def get_current_widget_key(
        self, ctx: ScriptRunContext, cache_type: CacheType
    ) -> str:
        state = ctx.session_state
        # Compute the key using only widgets that have values. A missing widget
        # can be ignored because we only care about getting different keys
        # for different widget values, and for that purpose doing nothing
        # to the running hash is just as good as including the widget with a
        # sentinel value. But by excluding it, we might get to reuse a result
        # saved before we knew about that widget.
        widget_values = [
            (wid, state[wid]) for wid in sorted(self.widget_ids) if wid in state
        ]
        widget_key = _make_widget_key(widget_values, cache_type)
        return widget_key