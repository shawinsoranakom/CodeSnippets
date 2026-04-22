def number_input(
        self,
        label: str,
        min_value: Optional[Number] = None,
        max_value: Optional[Number] = None,
        value: Union[NoValue, Number, None] = NoValue(),
        step: Optional[Number] = None,
        format: Optional[str] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
    ) -> Number:
        """Display a numeric input widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this input is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, Inline Code, Emojis, and Links.

            For accessibility reasons, you should never set an empty label (label="")
            but hide it with label_visibility if needed. In the future, we may disallow
            empty labels by raising an exception.
        min_value : int or float or None
            The minimum permitted value.
            If None, there will be no minimum.
        max_value : int or float or None
            The maximum permitted value.
            If None, there will be no maximum.
        value : int or float or None
            The value of this widget when it first renders.
            Defaults to min_value, or 0.0 if min_value is None
        step : int or float or None
            The stepping interval.
            Defaults to 1 if the value is an int, 0.01 otherwise.
            If the value is not specified, the format parameter will be used.
        format : str or None
            A printf-style format string controlling how the interface should
            display numbers. Output must be purely numeric. This does not impact
            the return value. Valid formatters: %d %e %f %g %i %u
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        help : str
            An optional tooltip that gets displayed next to the input.
        on_change : callable
            An optional callback invoked when this number_input's value changes.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        disabled : bool
            An optional boolean, which disables the number input if set to
            True. The default is False. This argument can only be supplied by
            keyword.
        label_visibility : "visible" or "hidden" or "collapsed"
            The visibility of the label. If "hidden", the label doesn't show but there
            is still empty space for it above the widget (equivalent to label="").
            If "collapsed", both the label and the space are removed. Default is
            "visible". This argument can only be supplied by keyword.

        Returns
        -------
        int or float
            The current value of the numeric input widget. The return type
            will match the data type of the value parameter.

        Example
        -------
        >>> number = st.number_input('Insert a number')
        >>> st.write('The current number is ', number)

        .. output::
           https://doc-number-input.streamlitapp.com/
           height: 260px

        """
        ctx = get_script_run_ctx()
        return self._number_input(
            label=label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=step,
            format=format,
            key=key,
            help=help,
            on_change=on_change,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            label_visibility=label_visibility,
            ctx=ctx,
        )