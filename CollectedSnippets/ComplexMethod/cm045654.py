def test_reducer():
    t = T(
        """
    pet  |  owner  | age
     1   | Alice   | 10
        """
    )
    assert repr(pw.reducers.min(t.pet)) == "pathway.reducers.min(<table1>.pet)"
    assert repr(pw.reducers.max(t.pet)) == "pathway.reducers.max(<table1>.pet)"
    assert repr(pw.reducers.sum(t.pet)) == "pathway.reducers.sum(<table1>.pet)"
    assert (
        repr(pw.reducers.sorted_tuple(t.pet))
        == "pathway.reducers.sorted_tuple(<table1>.pet, skip_nones=False)"
    )
    assert (
        repr(pw.reducers.tuple(t.pet, skip_nones=True))
        == "pathway.reducers.tuple(<table1>.pet, skip_nones=True)"
    )
    assert repr(pw.reducers.count()) == "pathway.reducers.count()"
    assert (
        repr(pw.reducers.argmin(t.pet))
        == "pathway.reducers.argmin(<table1>.pet, pathway.this.id)"
    )
    assert (
        repr(pw.reducers.argmax(t.pet))
        == "pathway.reducers.argmax(<table1>.pet, pathway.this.id)"
    )