def create_subplots(  # pylint: disable=too-many-arguments
        cls,
        rows: int = 1,
        cols: int = 1,
        shared_xaxes: bool = True,
        vertical_spacing: float | None = None,
        horizontal_spacing: float | None = None,
        subplot_titles: list[str] | tuple | None = None,
        row_width: list[float | int] | None = None,
        specs: list[list[dict[Any, Any] | None]] | None = None,
        **kwargs,
    ) -> "OpenBBFigure":
        """Create a new Plotly figure with subplots.

        Parameters
        ----------
        rows : `int`, optional
            Number of rows, by default 1
        cols : `int`, optional
            Number of columns, by default 1
        shared_xaxes : `bool`, optional
            Whether to share x axes, by default True
        vertical_spacing : `float`, optional
            Vertical spacing between subplots, by default None
        horizontal_spacing : `float`, optional
            Horizontal spacing between subplots, by default None
        subplot_titles : `Union[List[str], tuple]`, optional
            Titles for each subplot, by default None
        row_width : `List[Union[float, int]]`, optional
            Width of each row, by default [1]
        specs : `List[List[dict]]`, optional
            Subplot specs, by default `[[{}] * cols] * rows` (all subplots are the same size)
        """
        # We save the original kwargs to store them in the figure for later use
        subplots_kwargs = dict(
            rows=rows,
            cols=cols,
            shared_xaxes=shared_xaxes,
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing,
            subplot_titles=subplot_titles,
            row_width=row_width or [1] * rows,
            specs=specs or [[{}] * cols] * rows,
            **kwargs,
        )

        fig = make_subplots(**subplots_kwargs)  # type: ignore

        kwargs = {
            "multi_rows": rows > 1,
            "subplots_kwargs": subplots_kwargs,
        }
        if specs and any(
            spec.get("secondary_y", False) for row in specs for spec in row if spec
        ):
            kwargs["has_secondary_y"] = True

        return cls(fig, **kwargs)