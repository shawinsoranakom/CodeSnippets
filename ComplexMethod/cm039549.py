def test_check_preserve_type():
    # Ensures that type float32 is preserved.
    XA = np.resize(np.arange(40), (5, 8)).astype(np.float32)
    XB = np.resize(np.arange(40), (5, 8)).astype(np.float32)

    XA_checked, XB_checked = check_pairwise_arrays(XA, None)
    assert XA_checked.dtype == np.float32

    # both float32
    XA_checked, XB_checked = check_pairwise_arrays(XA, XB)
    assert XA_checked.dtype == np.float32
    assert XB_checked.dtype == np.float32

    # mismatched A
    XA_checked, XB_checked = check_pairwise_arrays(XA.astype(float), XB)
    assert XA_checked.dtype == float
    assert XB_checked.dtype == float

    # mismatched B
    XA_checked, XB_checked = check_pairwise_arrays(XA, XB.astype(float))
    assert XA_checked.dtype == float
    assert XB_checked.dtype == float