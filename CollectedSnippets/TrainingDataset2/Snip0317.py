def test_hash_map_is_the_same_as_dict(operations):
    my = HashMap(initial_block_size=4)
    py = {}
    for _, (fun, *args) in enumerate(operations):
        my_res, my_exc = _run_operation(my, fun, *args)
        py_res, py_exc = _run_operation(py, fun, *args)
        assert my_res == py_res
        assert str(my_exc) == str(py_exc)
        assert set(py) == set(my)
        assert len(py) == len(my)
        assert set(my.items()) == set(py.items())
