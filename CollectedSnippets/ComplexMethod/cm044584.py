def test_get_ansi_codes() -> None:
    assert Color.parse("default").get_ansi_codes() == ("39",)
    assert Color.parse("default").get_ansi_codes(False) == ("49",)
    assert Color.parse("red").get_ansi_codes() == ("31",)
    assert Color.parse("red").get_ansi_codes(False) == ("41",)
    assert Color.parse("color(1)").get_ansi_codes() == ("31",)
    assert Color.parse("color(1)").get_ansi_codes(False) == ("41",)
    assert Color.parse("#ff0000").get_ansi_codes() == ("38", "2", "255", "0", "0")
    assert Color.parse("#ff0000").get_ansi_codes(False) == ("48", "2", "255", "0", "0")