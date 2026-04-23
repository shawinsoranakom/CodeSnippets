def test_multilabel_hamming_loss():
    # Dense label indicator matrix format
    y1 = np.array([[0, 1, 1], [1, 0, 1]])
    y2 = np.array([[0, 0, 1], [1, 0, 1]])
    w = np.array([1, 3])

    assert hamming_loss(y1, y2) == 1 / 6
    assert hamming_loss(y1, y1) == 0
    assert hamming_loss(y2, y2) == 0
    assert hamming_loss(y2, 1 - y2) == 1
    assert hamming_loss(y1, 1 - y1) == 1
    assert hamming_loss(y1, np.zeros(y1.shape)) == 4 / 6
    assert hamming_loss(y2, np.zeros(y1.shape)) == 0.5
    assert hamming_loss(y1, y2, sample_weight=w) == 1.0 / 12
    assert hamming_loss(y1, 1 - y2, sample_weight=w) == 11.0 / 12
    assert hamming_loss(y1, np.zeros_like(y1), sample_weight=w) == 2.0 / 3
    # sp_hamming only works with 1-D arrays
    assert hamming_loss(y1[0], y2[0]) == sp_hamming(y1[0], y2[0])