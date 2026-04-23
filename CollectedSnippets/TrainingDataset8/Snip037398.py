def button(
        self,
        label: str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_click: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        type: Literal["primary", "secondary"] = "secondary",
        disabled: bool = False,
    ) -> bool:
        """Display a button widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this button is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, and Emojis.
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        help : str
            An optional tooltip that gets displayed when the button is
            hovered over.
        on_click : callable
            An optional callback invoked when this button is clicked.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        type : "secondary" or "primary"
            An optional string that specifies the button type. Can be "primary" for a
            button with additional emphasis or "secondary" for a normal button. This
            argument can only be supplied by keyword. Defaults to "secondary".
        disabled : bool
            An optional boolean, which disables the button if set to True. The
            default is False. This argument can only be supplied by keyword.

        Returns
        -------
        bool
            True if the button was clicked on the last run of the app,
            False otherwise.

        Example
        -------
        >>> if st.button('Say hello'):
        ...     st.write('Why hello there')
        ... else:
        ...     st.write('Goodbye')

        .. output::
           https://doc-buton.streamlitapp.com/
           height: 220px

        """
        key = to_key(key)
        ctx = get_script_run_ctx()

        # Checks whether the entered button type is one of the allowed options - either "primary" or "secondary"
        if type not in ["primary", "secondary"]:
            raise StreamlitAPIException(
                'The type argument to st.button must be "primary" or "secondary". \n'
                f'The argument passed was "{type}".'
            )

        return self.dg._button(
            label,
            key,
            help,
            is_form_submitter=False,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            type=type,
            ctx=ctx,
        )