def to_table(
        cls,
        data: "DataFrame",
        columnwidth: list[int | float] | None = None,
        print_index: bool = True,
        **kwargs,
    ) -> "OpenBBFigure":
        """Convert a dataframe to a table figure.

        Parameters
        ----------
        data : `DataFrame`
            The dataframe to convert
        columnwidth : `list`, optional
            The width of each column, by default None (auto)
        print_index : `bool`, optional
            Whether to print the index, by default True
        height : `int`, optional
            The height of the table, by default len(data.index) * 28 + 25
        width : `int`, optional
            The width of the table, by default sum(columnwidth) * 8.7

        Returns
        -------
        `plotly.graph_objects.Figure`
            The figure as a table
        """
        if not columnwidth:
            # we get the length of each column using the max length of the column
            # name and the max length of the column values as the column width
            columnwidth = [
                max(len(str(data[col].name)), data[col].astype(str).str.len().max())
                for col in data.columns
            ]
            # we add the length of the index column if we are printing the index
            if print_index:
                columnwidth.insert(
                    0,
                    max(
                        len(str(data.index.name)),
                        data.index.astype(str).str.len().max(),
                    ),
                )

            # we add a percentage of max to the min column width
            columnwidth = [
                int(x + (max(columnwidth) - min(columnwidth)) * 0.2)
                for x in columnwidth
            ]

        header_values, cell_values = cls._tbl_values(data, print_index)

        if (height := kwargs.get("height")) and height < len(data.index) * 28 + 25:
            kwargs.pop("height")
        if (width := kwargs.get("width")) and width < sum(columnwidth) * 8.7:
            kwargs.pop("width")

        height = kwargs.pop("height", len(data.index) * 28 + 25)
        width = kwargs.pop("width", sum(columnwidth) * 8.7)

        fig = OpenBBFigure()
        fig.add_table(
            header=dict(values=header_values),
            cells=dict(
                values=cell_values,
                align="left",
                height=25,
            ),
            columnwidth=columnwidth,
            **kwargs,
        )
        fig.update_layout(
            height=height,
            width=width,
            template="openbb_tables",
            margin=dict(l=0, r=0, b=0, t=0, pad=0),
            font=dict(size=14),
        )

        return fig