def test_truecolor() -> None:
    assert Color.parse("#ff0000").get_truecolor() == ColorTriplet(255, 0, 0)
    assert Color.parse("red").get_truecolor() == ColorTriplet(128, 0, 0)
    assert Color.parse("color(1)").get_truecolor() == ColorTriplet(128, 0, 0)
    assert Color.parse("color(17)").get_truecolor() == ColorTriplet(0, 0, 95)
    assert Color.parse("default").get_truecolor() == ColorTriplet(0, 0, 0)
    assert Color.parse("default").get_truecolor(foreground=False) == ColorTriplet(
        255, 255, 255
    )
    assert Color("red", ColorType.WINDOWS, number=1).get_truecolor() == ColorTriplet(
        197, 15, 31
    )