def test_markup_property():
    assert Text("").markup == ""
    assert Text("foo").markup == "foo"
    assert Text("foo", style="bold").markup == "[bold]foo[/bold]"
    assert Text.from_markup("foo [red]bar[/red]").markup == "foo [red]bar[/red]"
    assert (
        Text.from_markup("foo [red]bar[/red]", style="bold").markup
        == "[bold]foo [red]bar[/red][/bold]"
    )
    assert (
        Text.from_markup("[bold]foo [italic]bar[/bold] baz[/italic]").markup
        == "[bold]foo [italic]bar[/bold] baz[/italic]"
    )
    assert Text("[bold]foo").markup == "\\[bold]foo"