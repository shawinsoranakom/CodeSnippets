def show(  # noqa: PLR0915
        self,
        *args,
        external: bool = False,
        export_image: Path | str | None = "",  # pylint: disable=W0613
        **kwargs,
    ) -> "OpenBBFigure":
        """Show the figure.

        Parameters
        ----------
        external : `bool`, optional
            Whether to return the figure object instead of showing it, by default False
        export_image : `Union[Path, str]`, optional
            The path to export the figure image to, by default ""
        cmd_xshift : `int`, optional
            The x shift of the command source annotation, by default 0
        bar_width : `float`, optional
            The width of the bars, by default 0.0001
        date_xaxis : `bool`, optional
            Whether to check if the xaxis is a date axis, by default True
        """
        self.cmd_xshift = kwargs.pop("cmd_xshift", self.cmd_xshift)
        self.bar_width = kwargs.pop("bar_width", self.bar_width)

        if kwargs.pop("margin", True):
            self._adjust_margins()

        self._apply_feature_flags()
        if kwargs.pop("date_xaxis", True):
            self.add_rangebreaks()
            self._xaxis_tickformatstops()

        self.update_traces(marker_line_width=self.bar_width, selector=dict(type="bar"))
        self.update_traces(
            selector=dict(type="scatter", hovertemplate=None),
            hovertemplate="%{y}",
        )

        self.update_layout(
            newshape_line_color=(
                "gold" if self._theme.mapbox_style == "dark" else "#0d0887"
            ),
            modebar=dict(orientation="v"),
            spikedistance=2,
            hoverdistance=2,
        )

        if external:
            return self  # type: ignore

        if getattr(self._charting_settings, "headless", False):
            return self.to_json()  # type: ignore

        command_location = kwargs.pop("command_location", "")
        try:
            if self._backend is not None:
                return self._backend.send_figure(
                    fig=self, command_location=command_location
                )
        except Exception as e:
            warn(f"Failed to show figure with backend. {e}")

        return pio.show(self, *args, **kwargs)