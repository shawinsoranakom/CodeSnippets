def test_alpha():
    assert _Alpha('a') == _Alpha('a')
    assert _Alpha('a') == 'a'
    assert _Alpha('a') != _Alpha('b')
    assert _Alpha('a') != 1
    assert _Alpha('a') < _Alpha('b')
    assert _Alpha('a') < 'c'
    assert _Alpha('a') > _Numeric(1)
    with pytest.raises(ValueError):
        _Alpha('a') < None
    assert _Alpha('a') <= _Alpha('a')
    assert _Alpha('a') <= _Alpha('b')
    assert _Alpha('b') >= _Alpha('a')
    assert _Alpha('b') >= _Alpha('b')

    # The following 3*6 tests check that all comparison operators perform
    # as expected. DO NOT remove any of them, or reformulate them (to remove
    # the explicit `not`)!

    assert _Alpha('a') == _Alpha('a')
    assert not _Alpha('a') != _Alpha('a')  # pylint: disable=unneeded-not
    assert not _Alpha('a') < _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('a') <= _Alpha('a')
    assert not _Alpha('a') > _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('a') >= _Alpha('a')

    assert not _Alpha('a') == _Alpha('b')  # pylint: disable=unneeded-not
    assert _Alpha('a') != _Alpha('b')
    assert _Alpha('a') < _Alpha('b')
    assert _Alpha('a') <= _Alpha('b')
    assert not _Alpha('a') > _Alpha('b')  # pylint: disable=unneeded-not
    assert not _Alpha('a') >= _Alpha('b')  # pylint: disable=unneeded-not

    assert not _Alpha('b') == _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('b') != _Alpha('a')
    assert not _Alpha('b') < _Alpha('a')  # pylint: disable=unneeded-not
    assert not _Alpha('b') <= _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('b') > _Alpha('a')
    assert _Alpha('b') >= _Alpha('a')