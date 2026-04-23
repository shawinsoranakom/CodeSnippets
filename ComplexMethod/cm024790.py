def test_throttle() -> None:
    """Test the add cooldown decorator."""
    calls1 = []
    calls2 = []

    @util.Throttle(timedelta(seconds=4))
    def test_throttle1():
        calls1.append(1)

    @util.Throttle(timedelta(seconds=4), timedelta(seconds=2))
    def test_throttle2():
        calls2.append(1)

    now = dt_util.utcnow()
    plus3 = now + timedelta(seconds=3)
    plus5 = plus3 + timedelta(seconds=2)

    # Call first time and ensure methods got called
    test_throttle1()
    test_throttle2()

    assert len(calls1) == 1
    assert len(calls2) == 1

    # Call second time. Methods should not get called
    test_throttle1()
    test_throttle2()

    assert len(calls1) == 1
    assert len(calls2) == 1

    # Call again, overriding throttle, only first one should fire
    test_throttle1(no_throttle=True)
    test_throttle2(no_throttle=True)

    assert len(calls1) == 2
    assert len(calls2) == 1

    with patch("homeassistant.util.utcnow", return_value=plus3):
        test_throttle1()
        test_throttle2()

    assert len(calls1) == 2
    assert len(calls2) == 1

    with patch("homeassistant.util.utcnow", return_value=plus5):
        test_throttle1()
        test_throttle2()

    assert len(calls1) == 3
    assert len(calls2) == 2