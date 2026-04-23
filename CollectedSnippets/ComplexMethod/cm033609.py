def test_numeric():
    assert _Numeric(1) == _Numeric(1)
    assert _Numeric(1) == 1
    assert _Numeric(1) != _Numeric(2)
    assert _Numeric(1) != 'a'
    assert _Numeric(1) < _Numeric(2)
    assert _Numeric(1) < 3
    assert _Numeric(1) < _Alpha('b')
    with pytest.raises(ValueError):
        _Numeric(1) < None
    assert _Numeric(1) <= _Numeric(1)
    assert _Numeric(1) <= _Numeric(2)
    assert _Numeric(2) >= _Numeric(1)
    assert _Numeric(2) >= _Numeric(2)

    # The following 3*6 tests check that all comparison operators perform
    # as expected. DO NOT remove any of them, or reformulate them (to remove
    # the explicit `not`)!

    assert _Numeric(1) == _Numeric(1)
    assert not _Numeric(1) != _Numeric(1)  # pylint: disable=unneeded-not
    assert not _Numeric(1) < _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(1) <= _Numeric(1)
    assert not _Numeric(1) > _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(1) >= _Numeric(1)

    assert not _Numeric(1) == _Numeric(2)  # pylint: disable=unneeded-not
    assert _Numeric(1) != _Numeric(2)
    assert _Numeric(1) < _Numeric(2)
    assert _Numeric(1) <= _Numeric(2)
    assert not _Numeric(1) > _Numeric(2)  # pylint: disable=unneeded-not
    assert not _Numeric(1) >= _Numeric(2)  # pylint: disable=unneeded-not

    assert not _Numeric(2) == _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(2) != _Numeric(1)
    assert not _Numeric(2) < _Numeric(1)  # pylint: disable=unneeded-not
    assert not _Numeric(2) <= _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(2) > _Numeric(1)
    assert _Numeric(2) >= _Numeric(1)