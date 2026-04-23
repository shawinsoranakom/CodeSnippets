def test_query_repr_ellipsis():
    assert repr(Query(...)) == "Query(PydanticUndefined)"