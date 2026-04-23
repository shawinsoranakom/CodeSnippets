def multiselect(
        self,
        label: str,
        options: OptionSequence[T],
        default: Optional[Any] = None,
        format_func: Callable[[Any], Any] = str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        max_selections: Optional[int] = None,
    ) -> List[T]:
        """Display a multiselect widget.
        The multiselect widget starts as empty.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this select widget is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, Inline Code, Emojis, and Links.

            For accessibility reasons, you should never set an empty label (label="")
            but hide it with label_visibility if needed. In the future, we may disallow
            empty labels by raising an exception.
        options : Sequence[V], numpy.ndarray, pandas.Series, pandas.DataFrame, or pandas.Index
            Labels for the select options. This will be cast to str internally
            by default. For pandas.DataFrame, the first column is selected.
        default: [V], V, or None
            List of default values. Can also be a single value.
        format_func : function
            Function to modify the display of selectbox options. It receives
            the raw option as an argument and should output the label to be
            shown for that option. This has no impact on the return value of
            the multiselect.
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        help : str
            An optional tooltip that gets displayed next to the multiselect.
        on_change : callable
            An optional callback invoked when this multiselect's value changes.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        disabled : bool
            An optional boolean, which disables the multiselect widget if set
            to True. The default is False. This argument can only be supplied
            by keyword.
        label_visibility : "visible" or "hidden" or "collapsed"
            The visibility of the label. If "hidden", the label doesn't show but there
            is still empty space for it above the widget (equivalent to label="").
            If "collapsed", both the label and the space are removed. Default is
            "visible". This argument can only be supplied by keyword.
        max_selections : int
            The max selections that can be selected at a time.
            This argument can only be supplied by keyword.

        Returns
        -------
        list
            A list with the selected options

        Example
        -------
        >>> options = st.multiselect(
        ...     'What are your favorite colors',
        ...     ['Green', 'Yellow', 'Red', 'Blue'],
        ...     ['Yellow', 'Red'])
        >>>
        >>> st.write('You selected:', options)

        .. output::
           https://doc-multiselect.streamlitapp.com/
           height: 420px

        """
        ctx = get_script_run_ctx()
        return self._multiselect(
            label=label,
            options=options,
            default=default,
            format_func=format_func,
            key=key,
            help=help,
            on_change=on_change,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            label_visibility=label_visibility,
            ctx=ctx,
            max_selections=max_selections,
        )