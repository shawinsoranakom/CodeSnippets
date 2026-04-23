def test_parse_success() -> None:
    assert Color.parse("default") == Color("default", ColorType.DEFAULT, None, None)
    assert Color.parse("red") == Color("red", ColorType.STANDARD, 1, None)
    assert Color.parse("bright_red") == Color("bright_red", ColorType.STANDARD, 9, None)
    assert Color.parse("yellow4") == Color("yellow4", ColorType.EIGHT_BIT, 106, None)
    assert Color.parse("color(100)") == Color(
        "color(100)", ColorType.EIGHT_BIT, 100, None
    )
    assert Color.parse("#112233") == Color(
        "#112233", ColorType.TRUECOLOR, None, ColorTriplet(0x11, 0x22, 0x33)
    )
    assert Color.parse("rgb(90,100,110)") == Color(
        "rgb(90,100,110)", ColorType.TRUECOLOR, None, ColorTriplet(90, 100, 110)
    )