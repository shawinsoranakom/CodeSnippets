def form_submit_button(
        self,
        label: str = "Submit",
        help: Optional[str] = None,
        on_click=None,
        args=None,
        kwargs=None,
        *,  # keyword-only arguments:
        type: Literal["primary", "secondary"] = "secondary",
        disabled: bool = False,
    ) -> bool:
        """Display a form submit button.

        When this button is clicked, all widget values inside the form will be
        sent to Streamlit in a batch.

        Every form must have a form_submit_button. A form_submit_button
        cannot exist outside a form.

        For more information about forms, check out our
        `blog post <https://blog.streamlit.io/introducing-submit-button-and-forms/>`_.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this button is for.
            Defaults to "Submit".
        help : str or None
            A tooltip that gets displayed when the button is hovered over.
            Defaults to None.
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
            True if the button was clicked.
        """
        ctx = get_script_run_ctx()

        # Checks whether the entered button type is one of the allowed options - either "primary" or "secondary"
        if type not in ["primary", "secondary"]:
            raise StreamlitAPIException(
                'The type argument to st.button must be "primary" or "secondary". \n'
                f'The argument passed was "{type}".'
            )

        return self._form_submit_button(
            label=label,
            help=help,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
            type=type,
            disabled=disabled,
            ctx=ctx,
        )