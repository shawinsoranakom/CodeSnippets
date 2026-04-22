def _current_form(
    this_dg: "streamlit.delta_generator.DeltaGenerator",
) -> Optional[FormData]:
    """Find the FormData for the given DeltaGenerator.

    Forms are blocks, and can have other blocks nested inside them.
    To find the current form, we walk up the dg_stack until we find
    a DeltaGenerator that has FormData.
    """
    if not runtime.exists():
        return None

    if this_dg._form_data is not None:
        return this_dg._form_data

    if this_dg == this_dg._main_dg:
        # We were created via an `st.foo` call.
        # Walk up the dg_stack to see if we're nested inside a `with st.form` statement.
        ctx = get_script_run_ctx()
        if ctx is None or len(ctx.dg_stack) == 0:
            return None

        for dg in reversed(ctx.dg_stack):
            if dg._form_data is not None:
                return dg._form_data
    else:
        # We were created via an `dg.foo` call.
        # Take a look at our parent's form data to see if we're nested inside a form.
        parent = this_dg._parent
        if parent is not None and parent._form_data is not None:
            return parent._form_data

    return None