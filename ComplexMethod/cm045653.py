def test_column_binary_op():
    t = T(
        """
    pet  |  owner  | age
     1   | Alice   | 10
        """
    )
    assert repr(t.pet + t.age) == "(<table1>.pet + <table1>.age)"
    assert repr(t.pet - t.age) == "(<table1>.pet - <table1>.age)"
    assert repr(t.pet * t.age) == "(<table1>.pet * <table1>.age)"
    assert repr(t.pet / t.age) == "(<table1>.pet / <table1>.age)"
    assert repr(t.pet // t.age) == "(<table1>.pet // <table1>.age)"
    assert repr(t.pet**t.age) == "(<table1>.pet ** <table1>.age)"
    assert repr(t.pet % t.age) == "(<table1>.pet % <table1>.age)"
    assert repr(t.pet == t.age) == "(<table1>.pet == <table1>.age)"
    assert repr(t.pet != t.age) == "(<table1>.pet != <table1>.age)"
    assert repr(t.pet < t.age) == "(<table1>.pet < <table1>.age)"
    assert repr(t.pet <= t.age) == "(<table1>.pet <= <table1>.age)"
    assert repr(t.pet > t.age) == "(<table1>.pet > <table1>.age)"
    assert repr(t.pet >= t.age) == "(<table1>.pet >= <table1>.age)"