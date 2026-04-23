def checkbox(
        self,
        label: str,
        value: bool = False,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
    ) -> bool:
        """Display a checkbox widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this checkbox is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, Inline Code, Emojis, and Links.
        value : bool
            Preselect the checkbox when it first renders. This will be
            cast to bool internally.
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        help : str
            An optional tooltip that gets displayed next to the checkbox.
        on_change : callable
            An optional callback invoked when this checkbox's value changes.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        disabled : bool
            An optional boolean, which disables the checkbox if set to True.
            The default is False. This argument can only be supplied by keyword.

        Returns
        -------
        bool
            Whether or not the checkbox is checked.

        Example
        -------
        >>> import streamlit as st
        >>> agree = st.checkbox('I agree')
        >>>
        >>> if agree:
        ...     st.write('Great!')

        .. output::
           https://doc-checkbox.streamlitapp.com/
           height: 220px

        """
        ctx = get_script_run_ctx()
        return self._checkbox(
            label=label,
            value=value,
            key=key,
            help=help,
            on_change=on_change,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            ctx=ctx,
        )