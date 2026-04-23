def test_downgrade() -> None:
    assert Color.parse("color(9)").downgrade(0) == Color(
        "color(9)", ColorType.STANDARD, 9, None
    )

    assert Color.parse("#000000").downgrade(ColorSystem.EIGHT_BIT) == Color(
        "#000000", ColorType.EIGHT_BIT, 16, None
    )

    assert Color.parse("#ffffff").downgrade(ColorSystem.EIGHT_BIT) == Color(
        "#ffffff", ColorType.EIGHT_BIT, 231, None
    )

    assert Color.parse("#404142").downgrade(ColorSystem.EIGHT_BIT) == Color(
        "#404142", ColorType.EIGHT_BIT, 237, None
    )

    assert Color.parse("#ff0000").downgrade(ColorSystem.EIGHT_BIT) == Color(
        "#ff0000", ColorType.EIGHT_BIT, 196, None
    )

    assert Color.parse("#ff0000").downgrade(ColorSystem.STANDARD) == Color(
        "#ff0000", ColorType.STANDARD, 1, None
    )

    assert Color.parse("color(9)").downgrade(ColorSystem.STANDARD) == Color(
        "color(9)", ColorType.STANDARD, 9, None
    )

    assert Color.parse("color(20)").downgrade(ColorSystem.STANDARD) == Color(
        "color(20)", ColorType.STANDARD, 4, None
    )

    assert Color.parse("red").downgrade(ColorSystem.WINDOWS) == Color(
        "red", ColorType.WINDOWS, 1, None
    )

    assert Color.parse("bright_red").downgrade(ColorSystem.WINDOWS) == Color(
        "bright_red", ColorType.WINDOWS, 9, None
    )

    assert Color.parse("#ff0000").downgrade(ColorSystem.WINDOWS) == Color(
        "#ff0000", ColorType.WINDOWS, 1, None
    )

    assert Color.parse("color(255)").downgrade(ColorSystem.WINDOWS) == Color(
        "color(255)", ColorType.WINDOWS, 15, None
    )

    assert Color.parse("#00ff00").downgrade(ColorSystem.STANDARD) == Color(
        "#00ff00", ColorType.STANDARD, 2, None
    )