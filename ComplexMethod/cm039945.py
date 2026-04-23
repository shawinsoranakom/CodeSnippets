def test_sparse_device(csr_container, dispatch):
    np_arr = numpy.array([1])
    # For numpy < 2, the device attribute is not available on numpy arrays
    expected_numpy_array_device = getattr(np_arr, "device", None) if dispatch else None
    a, b = csr_container(numpy.array([[1]])), csr_container(numpy.array([[2]]))
    if dispatch and os.environ.get("SCIPY_ARRAY_API") is None:
        raise SkipTest("SCIPY_ARRAY_API is not set: not checking array_api input")
    with config_context(array_api_dispatch=dispatch):
        assert array_api_device(a, b) is None
        assert array_api_device(a, np_arr) == expected_numpy_array_device
        assert get_namespace_and_device(a, b)[2] is None
        assert get_namespace_and_device(a, np_arr)[2] == expected_numpy_array_device