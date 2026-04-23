def text_input(
        self,
        label: str,
        value: SupportsStr = "",
        max_chars: Optional[int] = None,
        key: Optional[Key] = None,
        type: str = "default",
        help: Optional[str] = None,
        autocomplete: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        placeholder: Optional[str] = None,
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
    ) -> str:
        """Display a single-line text input widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this input is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, Inline Code, Emojis, and Links.

            For accessibility reasons, you should never set an empty label (label="")
            but hide it with label_visibility if needed. In the future, we may disallow
            empty labels by raising an exception.
        value : object
            The text value of this widget when it first renders. This will be
            cast to str internally.
        max_chars : int or None
            Max number of characters allowed in text input.
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        type : str
            The type of the text input. This can be either "default" (for
            a regular text input), or "password" (for a text input that
            masks the user's typed value). Defaults to "default".
        help : str
            An optional tooltip that gets displayed next to the input.
        autocomplete : str
            An optional value that will be passed to the <input> element's
            autocomplete property. If unspecified, this value will be set to
            "new-password" for "password" inputs, and the empty string for
            "default" inputs. For more details, see https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete
        on_change : callable
            An optional callback invoked when this text_input's value changes.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        placeholder : str or None
            An optional string displayed when the text input is empty. If None,
            no text is displayed. This argument can only be supplied by keyword.
        disabled : bool
            An optional boolean, which disables the text input if set to True.
            The default is False. This argument can only be supplied by keyword.
        label_visibility : "visible" or "hidden" or "collapsed"
            The visibility of the label. If "hidden", the label doesn't show but there
            is still empty space for it above the widget (equivalent to label="").
            If "collapsed", both the label and the space are removed. Default is
            "visible". This argument can only be supplied by keyword.

        Returns
        -------
        str
            The current value of the text input widget.

        Example
        -------
        >>> title = st.text_input('Movie title', 'Life of Brian')
        >>> st.write('The current movie title is', title)

        .. output::
           https://doc-text-input.streamlitapp.com/
           height: 260px

        """
        ctx = get_script_run_ctx()
        return self._text_input(
            label=label,
            value=value,
            max_chars=max_chars,
            key=key,
            type=type,
            help=help,
            autocomplete=autocomplete,
            on_change=on_change,
            args=args,
            kwargs=kwargs,
            placeholder=placeholder,
            disabled=disabled,
            label_visibility=label_visibility,
            ctx=ctx,
        )