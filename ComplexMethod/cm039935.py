def test_raises():
    # Tests for the raises context manager

    # Proper type, no match
    with raises(TypeError):
        raise TypeError()

    # Proper type, proper match
    with raises(TypeError, match="how are you") as cm:
        raise TypeError("hello how are you")
    assert cm.raised_and_matched

    # Proper type, proper match with multiple patterns
    with raises(TypeError, match=["not this one", "how are you"]) as cm:
        raise TypeError("hello how are you")
    assert cm.raised_and_matched

    # bad type, no match
    with pytest.raises(ValueError, match="this will be raised"):
        with raises(TypeError) as cm:
            raise ValueError("this will be raised")
    assert not cm.raised_and_matched

    # Bad type, no match, with an err_msg
    with pytest.raises(AssertionError, match="the failure message"):
        with raises(TypeError, err_msg="the failure message") as cm:
            raise ValueError()
    assert not cm.raised_and_matched

    # bad type, with match (is ignored anyway)
    with pytest.raises(ValueError, match="this will be raised"):
        with raises(TypeError, match="this is ignored") as cm:
            raise ValueError("this will be raised")
    assert not cm.raised_and_matched

    # proper type but bad match
    with pytest.raises(
        AssertionError, match="should contain one of the following patterns"
    ):
        with raises(TypeError, match="hello") as cm:
            raise TypeError("Bad message")
    assert not cm.raised_and_matched

    # proper type but bad match, with err_msg
    with pytest.raises(AssertionError, match="the failure message"):
        with raises(TypeError, match="hello", err_msg="the failure message") as cm:
            raise TypeError("Bad message")
    assert not cm.raised_and_matched

    # no raise with default may_pass=False
    with pytest.raises(AssertionError, match="Did not raise"):
        with raises(TypeError) as cm:
            pass
    assert not cm.raised_and_matched

    # no raise with may_pass=True
    with raises(TypeError, match="hello", may_pass=True) as cm:
        pass  # still OK
    assert not cm.raised_and_matched

    # Multiple exception types:
    with raises((TypeError, ValueError)):
        raise TypeError()
    with raises((TypeError, ValueError)):
        raise ValueError()
    with pytest.raises(AssertionError):
        with raises((TypeError, ValueError)):
            pass