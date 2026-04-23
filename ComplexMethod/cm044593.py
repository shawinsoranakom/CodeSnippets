def render_tables():
    console = Console(
        width=60,
        force_terminal=True,
        file=io.StringIO(),
        legacy_windows=False,
        color_system=None,
        _environ={},
    )

    table = Table(title="test table", caption="table caption", expand=False)
    table.add_column("foo", footer=Text("total"), no_wrap=True, overflow="ellipsis")
    table.add_column("bar", justify="center")
    table.add_column("baz", justify="right")

    table.add_row("Averlongwordgoeshere", "banana pancakes", None)

    assert Measurement.get(console, console.options, table) == Measurement(41, 48)
    table.expand = True
    assert Measurement.get(console, console.options, table) == Measurement(41, 48)

    for width in range(10, 60, 5):
        console.print(table, width=width)

    table.expand = False
    console.print(table, justify="left")
    console.print(table, justify="center")
    console.print(table, justify="right")

    assert table.row_count == 1

    table.row_styles = ["red", "yellow"]
    table.add_row("Coffee")
    table.add_row("Coffee", "Chocolate", None, "cinnamon")

    assert table.row_count == 3

    console.print(table)

    table.show_lines = True
    console.print(table)

    table.show_footer = True
    console.print(table)

    table.show_edge = False

    console.print(table)

    table.padding = 1
    console.print(table)

    table.width = 20
    assert Measurement.get(console, console.options, table) == Measurement(20, 20)
    table.expand = False
    assert Measurement.get(console, console.options, table) == Measurement(20, 20)
    table.expand = True
    console.print(table)

    table.columns[0].no_wrap = True
    table.columns[1].no_wrap = True
    table.columns[2].no_wrap = True

    console.print(table)

    table.padding = 0
    table.width = 60
    table.leading = 1
    console.print(table)

    return console.file.getvalue()