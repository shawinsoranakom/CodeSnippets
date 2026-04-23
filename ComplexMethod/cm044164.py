def add_legend_label(  # noqa: PLR0913
        self,
        trace: str | None = None,
        label: str | None = None,
        mode: str | None = None,
        marker: dict | None = None,
        line_dash: str | None = None,
        legendrank: int | None = None,
        **kwargs,
    ) -> None:
        """Add a legend label.

        Parameters
        ----------
        trace : `str`, optional
            The name of the trace to use as a template, by default None
        label : `str`, optional
            The label to use, by default None (uses the trace name if trace is specified)
            If trace is not specified, label must be specified
        mode : `str`, optional
            The mode to use, by default "lines" (uses the trace mode if trace is specified)
        marker : `dict`, optional
            The marker to use, by default dict() (uses the trace marker if trace is specified)
        line_dash : `str`, optional
            The line dash to use, by default "solid" (uses the trace line dash if trace is specified)
        legendrank : `int`, optional
            The legend rank, by default None (e.g. 1 is above 2)

        Raises
        ------
        ValueError
            If trace is not found
        ValueError
            If label is not specified and trace is not specified
        """
        if trace:
            for trace_ in self.data:
                if trace_.name == trace:  # type: ignore
                    for arg, default in zip(
                        [label, mode, marker, line_dash],
                        [trace, trace_.mode, trace_.marker, trace_.line_dash],  # type: ignore
                    ):
                        if not arg and default:
                            arg = default  # noqa: PLW2901

                    kwargs.update(dict(yaxis=trace_.yaxis))  # type: ignore
                    break
            else:
                raise ValueError(f"Trace '{trace}' not found")

        if not label:
            raise ValueError("Label must be specified")

        self.add_scatter(
            x=[None],
            y=[None],
            mode=mode or "lines",
            name=label,
            marker=marker or dict(),
            line_dash=line_dash or "solid",
            legendrank=legendrank,
            **kwargs,
        )