def _create_rich_table(
    shape: ShapeType,
    shards: list[tuple[tuple[int, int], tuple[int, int], int]],
    device_kind: str = "",
    scale: float = 1.0,
    min_width: int = 9,
    max_width: int = 80,
):
    import matplotlib
    import rich.align
    import rich.box
    import rich.console
    import rich.padding
    import rich.style
    import rich.table

    dtensor_height = shape[0]
    dtensor_width = shape[1] if len(shape) == 2 else 1

    row_ranges = sorted({s[0] for s in shards})
    col_ranges = sorted({s[1] for s in shards})
    num_rows, num_cols = len(row_ranges), len(col_ranges)

    console = rich.console.Console(width=max_width)
    use_color = console.color_system
    color_iter = make_color_iter(matplotlib.colormaps["tab20b"], num_rows, num_cols)

    base_height = int(10 * scale)
    aspect_ratio = (shape[1] if len(shape) == 2 else 1) / shape[0]
    base_width = int(base_height * aspect_ratio)
    height_to_width_ratio = 2.5

    table = rich.table.Table(
        show_header=False,
        show_lines=not use_color,
        padding=0,
        highlight=not use_color,
        pad_edge=False,
        box=rich.box.SQUARE if not use_color else None,
    )
    for row in range(num_rows):
        table_row = []
        for col in range(num_cols):
            entry = (
                device_kind
                + ":"
                + ",".join(
                    [
                        str(device_id)
                        for row_range, col_range, device_id in shards
                        if row_range == row_ranges[row] and col_range == col_ranges[col]
                    ]
                )
            )
            width = (col_ranges[col][1] - col_ranges[col][0]) / dtensor_width
            width = int(width * base_width * height_to_width_ratio)
            height = (row_ranges[row][1] - row_ranges[row][0]) / dtensor_height
            height = int(height * base_height)
            left_padding, remainder = divmod(width - len(entry) - 2, 2)
            right_padding = left_padding + remainder
            top_padding, remainder = divmod(height - 2, 2)
            bottom_padding = top_padding + remainder
            if use_color:
                color = _canonicalize_color(next(color_iter)[:3])
                text_color = _get_text_color(color)
                top_padding += 1
                bottom_padding += 1
                left_padding += 1
                right_padding += 1
            else:
                color = None
                text_color = None
            padding = (
                max(top_padding, 0),
                max(right_padding, 0),
                max(bottom_padding, 0),
                max(left_padding, 0),
            )
            table_row.append(
                rich.padding.Padding(
                    rich.align.Align(entry, "center", vertical="middle"),
                    padding,
                    style=rich.style.Style(bgcolor=color, color=text_color),
                )
            )
        table.add_row(*table_row)
    console.print(table, end="\n\n")