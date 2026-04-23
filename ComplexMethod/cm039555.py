def test_multilabel_zero_one_loss_subset():
    # Dense label indicator matrix format
    y1 = np.array([[0, 1, 1], [1, 0, 1]])
    y2 = np.array([[0, 0, 1], [1, 0, 1]])

    assert zero_one_loss(y1, y2) == 0.5
    assert zero_one_loss(y1, y1) == 0
    assert zero_one_loss(y2, y2) == 0
    assert zero_one_loss(y2, np.logical_not(y2)) == 1
    assert zero_one_loss(y1, np.logical_not(y1)) == 1
    assert zero_one_loss(y1, np.zeros(y1.shape)) == 1
    assert zero_one_loss(y2, np.zeros(y1.shape)) == 1