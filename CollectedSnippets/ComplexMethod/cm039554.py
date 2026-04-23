def test_confusion_matrix_dtype():
    y = [0, 1, 1]
    weight = np.ones(len(y))
    # confusion_matrix returns int64 by default
    cm = confusion_matrix(y, y)
    assert cm.dtype == np.int64
    # The dtype of confusion_matrix is always 64 bit
    for dtype in [np.bool_, np.int32, np.uint64]:
        cm = confusion_matrix(y, y, sample_weight=weight.astype(dtype, copy=False))
        assert cm.dtype == np.int64
    for dtype in [np.float32, np.float64, None, object]:
        cm = confusion_matrix(y, y, sample_weight=weight.astype(dtype, copy=False))
        assert cm.dtype == np.float64

    # np.iinfo(np.uint32).max should be accumulated correctly
    weight = np.full(len(y), 4294967295, dtype=np.uint32)
    cm = confusion_matrix(y, y, sample_weight=weight)
    assert cm[0, 0] == 4294967295
    assert cm[1, 1] == 8589934590

    # np.iinfo(np.int64).max should cause an overflow
    weight = np.full(len(y), 9223372036854775807, dtype=np.int64)
    cm = confusion_matrix(y, y, sample_weight=weight)
    assert cm[0, 0] == 9223372036854775807
    assert cm[1, 1] == -2