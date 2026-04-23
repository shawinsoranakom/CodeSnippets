def test_incremental_variance_numerical_stability():
    # Test Youngs and Cramer incremental variance formulas.

    def np_var(A):
        return A.var(axis=0)

    # Naive one pass variance computation - not numerically stable
    # https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
    def one_pass_var(X):
        n = X.shape[0]
        exp_x2 = (X**2).sum(axis=0) / n
        expx_2 = (X.sum(axis=0) / n) ** 2
        return exp_x2 - expx_2

    # Two-pass algorithm, stable.
    # We use it as a benchmark. It is not an online algorithm
    # https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Two-pass_algorithm
    def two_pass_var(X):
        mean = X.mean(axis=0)
        Y = X.copy()
        return np.mean((Y - mean) ** 2, axis=0)

    # Naive online implementation
    # https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
    # This works only for chunks for size 1
    def naive_mean_variance_update(x, last_mean, last_variance, last_sample_count):
        updated_sample_count = last_sample_count + 1
        samples_ratio = last_sample_count / float(updated_sample_count)
        updated_mean = x / updated_sample_count + last_mean * samples_ratio
        updated_variance = (
            last_variance * samples_ratio
            + (x - last_mean) * (x - updated_mean) / updated_sample_count
        )
        return updated_mean, updated_variance, updated_sample_count

    # We want to show a case when one_pass_var has error > 1e-3 while
    # _batch_mean_variance_update has less.
    tol = 200
    n_features = 2
    n_samples = 10000
    x1 = np.array(1e8, dtype=np.float64)
    x2 = np.log(1e-5, dtype=np.float64)
    A0 = np.full((n_samples // 2, n_features), x1, dtype=np.float64)
    A1 = np.full((n_samples // 2, n_features), x2, dtype=np.float64)
    A = np.vstack((A0, A1))

    # Naive one pass var: >tol (=1063)
    assert np.abs(np_var(A) - one_pass_var(A)).max() > tol

    # Starting point for online algorithms: after A0

    # Naive implementation: >tol (436)
    mean, var, n = A0[0, :], np.zeros(n_features), n_samples // 2
    for i in range(A1.shape[0]):
        mean, var, n = naive_mean_variance_update(A1[i, :], mean, var, n)
    assert n == A.shape[0]
    # the mean is also slightly unstable
    assert np.abs(A.mean(axis=0) - mean).max() > 1e-6
    assert np.abs(np_var(A) - var).max() > tol

    # Robust implementation: <tol (177)
    mean, var = A0[0, :], np.zeros(n_features)
    n = np.full(n_features, n_samples // 2, dtype=np.int32)
    for i in range(A1.shape[0]):
        mean, var, n = _incremental_mean_and_var(
            A1[i, :].reshape((1, A1.shape[1])), mean, var, n
        )
    assert_array_equal(n, A.shape[0])
    assert_array_almost_equal(A.mean(axis=0), mean)
    assert tol > np.abs(np_var(A) - var).max()