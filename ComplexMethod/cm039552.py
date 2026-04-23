def test_precision_recall_f_binary_single_class():
    # Test precision, recall and F-scores behave with a single positive or
    # negative class
    # Such a case may occur with non-stratified cross-validation
    assert 1.0 == precision_score([1, 1], [1, 1])
    assert 1.0 == recall_score([1, 1], [1, 1])
    assert 1.0 == f1_score([1, 1], [1, 1])
    assert 1.0 == fbeta_score([1, 1], [1, 1], beta=0)

    assert 0.0 == precision_score([-1, -1], [-1, -1])
    assert 0.0 == recall_score([-1, -1], [-1, -1])
    assert 0.0 == f1_score([-1, -1], [-1, -1])
    assert 0.0 == fbeta_score([-1, -1], [-1, -1], beta=float("inf"))
    assert fbeta_score([-1, -1], [-1, -1], beta=float("inf")) == pytest.approx(
        fbeta_score([-1, -1], [-1, -1], beta=1e5)
    )