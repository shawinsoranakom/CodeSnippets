def test_suggestions():
    assert _get_suggestions("one") == ['one']
    assert _get_suggestions("one or two") == ['one', 'two']
    assert _get_suggestions("one, two or three") == ['one', 'two', 'three']