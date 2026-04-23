def test_immutable_list():
    l1 = ImmutableList([1, 2, 3])

    assert list(l1) == [1, 2, 3]
    assert l1[0] == 1
    assert l1[1] == 2
    assert list(l1) == [1, 2, 3]
    assert len(l1) == 3

    assert 2 in l1
    assert 99 not in l1
    assert l1.count(1) == 1
    assert l1.count(99) == 0
    assert l1.index(2) == 1
    assert list(reversed(l1)) == [3, 2, 1]

    with pytest.raises(Exception) as exc:
        l1[0] = "foo"
    exc.match("does not support item assignment")
    with pytest.raises(Exception) as exc:
        l1.append("foo")