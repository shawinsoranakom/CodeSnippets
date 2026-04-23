def test_exactly_zero_info_score():
    # Check numerical stability when information is exactly zero
    for i in np.logspace(1, 4, 4).astype(int):
        labels_a, labels_b = (np.ones(i, dtype=int), np.arange(i, dtype=int))
        assert normalized_mutual_info_score(labels_a, labels_b) == pytest.approx(0.0)
        assert v_measure_score(labels_a, labels_b) == pytest.approx(0.0)
        assert adjusted_mutual_info_score(labels_a, labels_b) == 0.0
        assert normalized_mutual_info_score(labels_a, labels_b) == pytest.approx(0.0)
        for method in ["min", "geometric", "arithmetic", "max"]:
            assert (
                adjusted_mutual_info_score(labels_a, labels_b, average_method=method)
                == 0.0
            )
            assert normalized_mutual_info_score(
                labels_a, labels_b, average_method=method
            ) == pytest.approx(0.0)