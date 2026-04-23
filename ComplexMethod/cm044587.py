def test_str():
    assert str(Style(bold=False)) == "not bold"
    assert str(Style(color="red", bold=False)) == "not bold red"
    assert str(Style(color="red", bold=False, italic=True)) == "not bold italic red"
    assert str(Style()) == "none"
    assert str(Style(bold=True)) == "bold"
    assert str(Style(color="red", bold=True)) == "bold red"
    assert str(Style(color="red", bgcolor="black", bold=True)) == "bold red on black"
    all_styles = Style(
        color="red",
        bgcolor="black",
        bold=True,
        dim=True,
        italic=True,
        underline=True,
        blink=True,
        blink2=True,
        reverse=True,
        conceal=True,
        strike=True,
        underline2=True,
        frame=True,
        encircle=True,
        overline=True,
    )
    expected = "bold dim italic underline blink blink2 reverse conceal strike underline2 frame encircle overline red on black"
    assert str(all_styles) == expected
    assert str(Style(link="foo")) == "link foo"