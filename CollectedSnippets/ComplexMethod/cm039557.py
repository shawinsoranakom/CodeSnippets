def test_multilabel_jaccard_score(recwarn):
    # Dense label indicator matrix format
    y1 = np.array([[0, 1, 1], [1, 0, 1]])
    y2 = np.array([[0, 0, 1], [1, 0, 1]])

    # size(y1 \inter y2) = [1, 2]
    # size(y1 \union y2) = [2, 2]

    assert jaccard_score(y1, y2, average="samples") == 0.75
    assert jaccard_score(y1, y1, average="samples") == 1
    assert jaccard_score(y2, y2, average="samples") == 1
    assert jaccard_score(y2, np.logical_not(y2), average="samples") == 0
    assert jaccard_score(y1, np.logical_not(y1), average="samples") == 0
    assert jaccard_score(y1, np.zeros(y1.shape), average="samples") == 0
    assert jaccard_score(y2, np.zeros(y1.shape), average="samples") == 0

    y_true = np.array([[0, 1, 1], [1, 0, 0]])
    y_pred = np.array([[1, 1, 1], [1, 0, 1]])
    # average='macro'
    assert_almost_equal(jaccard_score(y_true, y_pred, average="macro"), 2.0 / 3)
    # average='micro'
    assert_almost_equal(jaccard_score(y_true, y_pred, average="micro"), 3.0 / 5)
    # average='samples'
    assert_almost_equal(jaccard_score(y_true, y_pred, average="samples"), 7.0 / 12)
    assert_almost_equal(
        jaccard_score(y_true, y_pred, average="samples", labels=[0, 2]), 1.0 / 2
    )
    assert_almost_equal(
        jaccard_score(y_true, y_pred, average="samples", labels=[1, 2]), 1.0 / 2
    )
    # average=None
    assert_array_equal(
        jaccard_score(y_true, y_pred, average=None), np.array([1.0 / 2, 1.0, 1.0 / 2])
    )

    y_true = np.array([[0, 1, 1], [1, 0, 1]])
    y_pred = np.array([[1, 1, 1], [1, 0, 1]])
    assert_almost_equal(jaccard_score(y_true, y_pred, average="macro"), 5.0 / 6)
    # average='weighted'
    assert_almost_equal(jaccard_score(y_true, y_pred, average="weighted"), 7.0 / 8)

    msg2 = "Got 4 > 2"
    with pytest.raises(ValueError, match=msg2):
        jaccard_score(y_true, y_pred, labels=[4], average="macro")
    msg3 = "Got -1 < 0"
    with pytest.raises(ValueError, match=msg3):
        jaccard_score(y_true, y_pred, labels=[-1], average="macro")

    msg = (
        "Jaccard is ill-defined and being set to 0.0 in labels "
        "with no true or predicted samples."
    )

    with pytest.warns(UndefinedMetricWarning, match=msg):
        assert (
            jaccard_score(np.array([[0, 1]]), np.array([[0, 1]]), average="macro")
            == 0.5
        )

    msg = (
        "Jaccard is ill-defined and being set to 0.0 in samples "
        "with no true or predicted labels."
    )

    with pytest.warns(UndefinedMetricWarning, match=msg):
        assert (
            jaccard_score(
                np.array([[0, 0], [1, 1]]),
                np.array([[0, 0], [1, 1]]),
                average="samples",
            )
            == 0.5
        )

    assert not list(recwarn)