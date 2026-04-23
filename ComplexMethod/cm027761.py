def get_grid(
        self,
        n_rows: int,
        n_cols: int,
        height: float | None = None,
        width: float | None = None,
        group_by_rows: bool = False,
        group_by_cols: bool = False,
        **kwargs
    ) -> Self:
        """
        Returns a new mobject containing multiple copies of this one
        arranged in a grid
        """
        total = n_rows * n_cols
        grid = self.replicate(total)
        if group_by_cols:
            kwargs["fill_rows_first"] = False
        grid.arrange_in_grid(n_rows, n_cols, **kwargs)
        if height is not None:
            grid.set_height(height)
        if width is not None:
            grid.set_height(width)

        group_class = self.get_group_class()
        if group_by_rows:
            return group_class(*(grid[n:n + n_cols] for n in range(0, total, n_cols)))
        elif group_by_cols:
            return group_class(*(grid[n:n + n_rows] for n in range(0, total, n_rows)))
        else:
            return grid