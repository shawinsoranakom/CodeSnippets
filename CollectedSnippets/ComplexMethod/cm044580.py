def test_deque() -> None:
    test_deque = deque([1, 2, 3])
    result = pretty_repr(test_deque)
    assert result == "deque([1, 2, 3])"
    test_deque = deque([1, 2, 3], maxlen=None)
    result = pretty_repr(test_deque)
    assert result == "deque([1, 2, 3])"
    test_deque = deque([1, 2, 3], maxlen=5)
    result = pretty_repr(test_deque)
    assert result == "deque([1, 2, 3], maxlen=5)"
    test_deque = deque([1, 2, 3], maxlen=0)
    result = pretty_repr(test_deque)
    assert result == "deque(maxlen=0)"
    test_deque = deque([])
    result = pretty_repr(test_deque)
    assert result == "deque()"
    test_deque = deque([], maxlen=None)
    result = pretty_repr(test_deque)
    assert result == "deque()"
    test_deque = deque([], maxlen=5)
    result = pretty_repr(test_deque)
    assert result == "deque(maxlen=5)"
    test_deque = deque([], maxlen=0)
    result = pretty_repr(test_deque)
    assert result == "deque(maxlen=0)"