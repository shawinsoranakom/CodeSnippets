def test_multilabel_accuracy_score_subset_accuracy():
    # Dense label indicator matrix format
    y1 = np.array([[0, 1, 1], [1, 0, 1]])
    y2 = np.array([[0, 0, 1], [1, 0, 1]])

    assert accuracy_score(y1, y2) == 0.5
    assert accuracy_score(y1, y1) == 1
    assert accuracy_score(y2, y2) == 1
    assert accuracy_score(y2, np.logical_not(y2)) == 0
    assert accuracy_score(y1, np.logical_not(y1)) == 0
    assert accuracy_score(y1, np.zeros(y1.shape)) == 0
    assert accuracy_score(y2, np.zeros(y1.shape)) == 0