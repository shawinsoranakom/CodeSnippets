def test_matthews_corrcoef_against_jurman(global_random_seed):
    # Check that the multiclass matthews_corrcoef agrees with the definition
    # presented in Jurman, Riccadonna, Furlanello, (2012). A Comparison of MCC
    # and CEN Error Measures in MultiClass Prediction
    rng = np.random.RandomState(global_random_seed)
    y_true = rng.randint(0, 2, size=20)
    y_pred = rng.randint(0, 2, size=20)
    sample_weight = rng.rand(20)

    C = confusion_matrix(y_true, y_pred, sample_weight=sample_weight)
    N = len(C)
    cov_ytyp = sum(
        [
            C[k, k] * C[m, l] - C[l, k] * C[k, m]
            for k in range(N)
            for m in range(N)
            for l in range(N)
        ]
    )
    cov_ytyt = sum(
        [
            C[:, k].sum()
            * np.sum([C[g, f] for f in range(N) for g in range(N) if f != k])
            for k in range(N)
        ]
    )
    cov_ypyp = np.sum(
        [
            C[k, :].sum()
            * np.sum([C[f, g] for f in range(N) for g in range(N) if f != k])
            for k in range(N)
        ]
    )
    mcc_jurman = cov_ytyp / np.sqrt(cov_ytyt * cov_ypyp)
    mcc_ours = matthews_corrcoef(y_true, y_pred, sample_weight=sample_weight)

    assert_almost_equal(mcc_ours, mcc_jurman, 10)