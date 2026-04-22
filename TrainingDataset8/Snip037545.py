def metric(
        self,
        label: str,
        value: Value,
        delta: Delta = None,
        delta_color: DeltaColor = "normal",
        help: Optional[str] = None,
    ) -> "DeltaGenerator":
        """Display a metric in big bold font, with an optional indicator of how the metric changed.

        Tip: If you want to display a large number, it may be a good idea to
        shorten it using packages like `millify <https://github.com/azaitsev/millify>`_
        or `numerize <https://github.com/davidsa03/numerize>`_. E.g. ``1234`` can be
        displayed as ``1.2k`` using ``st.metric("Short number", millify(1234))``.

        Parameters
        ----------
        label : str
            The header or title for the metric. The label can optionally contain
            Markdown and supports the following elements: Bold, Italics,
            Strikethroughs, Inline Code, Emojis, and Links.
        value : int, float, str, or None
             Value of the metric. None is rendered as a long dash.
        delta : int, float, str, or None
            Indicator of how the metric changed, rendered with an arrow below
            the metric. If delta is negative (int/float) or starts with a minus
            sign (str), the arrow points down and the text is red; else the
            arrow points up and the text is green. If None (default), no delta
            indicator is shown.
        delta_color : str
             If "normal" (default), the delta indicator is shown as described
             above. If "inverse", it is red when positive and green when
             negative. This is useful when a negative change is considered
             good, e.g. if cost decreased. If "off", delta is  shown in gray
             regardless of its value.
        help : str
            An optional tooltip that gets displayed next to the metric label.

        Example
        -------
        >>> st.metric(label="Temperature", value="70 °F", delta="1.2 °F")

        .. output::
            https://doc-metric-example1.streamlitapp.com/
            height: 210px

        ``st.metric`` looks especially nice in combination with ``st.columns``:

        >>> col1, col2, col3 = st.columns(3)
        >>> col1.metric("Temperature", "70 °F", "1.2 °F")
        >>> col2.metric("Wind", "9 mph", "-8%")
        >>> col3.metric("Humidity", "86%", "4%")

        .. output::
            https://doc-metric-example2.streamlitapp.com/
            height: 210px

        The delta indicator color can also be inverted or turned off:

        >>> st.metric(label="Gas price", value=4, delta=-0.5,
        ...     delta_color="inverse")
        >>>
        >>> st.metric(label="Active developers", value=123, delta=123,
        ...     delta_color="off")

        .. output::
            https://doc-metric-example3.streamlitapp.com/
            height: 320px

        """
        metric_proto = MetricProto()
        metric_proto.body = self.parse_value(value)
        metric_proto.label = self.parse_label(label)
        metric_proto.delta = self.parse_delta(delta)
        if help is not None:
            metric_proto.help = dedent(help)

        color_and_direction = self.determine_delta_color_and_direction(
            cast(DeltaColor, clean_text(delta_color)), delta
        )
        metric_proto.color = color_and_direction.color
        metric_proto.direction = color_and_direction.direction

        return self.dg._enqueue("metric", metric_proto)