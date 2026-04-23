def test_clear_meta_and_links():
    style = Style.parse("bold red on black link https://example.org") + Style.on(
        click="CLICK"
    )

    assert style.meta == {"@click": "CLICK"}
    assert style.link == "https://example.org"
    assert style.color == Color.parse("red")
    assert style.bgcolor == Color.parse("black")
    assert style.bold
    assert not style.italic

    clear_style = style.clear_meta_and_links()

    assert clear_style.meta == {}
    assert clear_style.link == None
    assert clear_style.color == Color.parse("red")
    assert clear_style.bgcolor == Color.parse("black")
    assert clear_style.bold
    assert not clear_style.italic