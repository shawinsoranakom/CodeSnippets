def bench_b(power_list):
    n_samples, n_features = 1000, 10000
    data_params = {
        "n_samples": n_samples,
        "n_features": n_features,
        "tail_strength": 0.7,
        "random_state": random_state,
    }
    dataset_name = "low rank matrix %d x %d" % (n_samples, n_features)
    ranks = [10, 50, 100]

    if enable_spectral_norm:
        all_spectral = defaultdict(list)
    all_frobenius = defaultdict(list)
    for rank in ranks:
        X = make_low_rank_matrix(effective_rank=rank, **data_params)
        if enable_spectral_norm:
            X_spectral_norm = norm_diff(X, norm=2, msg=False, random_state=0)
        X_fro_norm = norm_diff(X, norm="fro", msg=False)

        for n_comp in [int(rank / 2), rank, rank * 2]:
            label = "rank=%d, n_comp=%d" % (rank, n_comp)
            print(label)
            for pi in power_list:
                U, s, V, _ = svd_timing(
                    X,
                    n_comp,
                    n_iter=pi,
                    n_oversamples=2,
                    power_iteration_normalizer="LU",
                )
                if enable_spectral_norm:
                    A = U.dot(np.diag(s).dot(V))
                    all_spectral[label].append(
                        norm_diff(X - A, norm=2, random_state=0) / X_spectral_norm
                    )
                f = scalable_frobenius_norm_discrepancy(X, U, s, V)
                all_frobenius[label].append(f / X_fro_norm)

    if enable_spectral_norm:
        title = "%s: spectral norm diff vs n power iteration" % (dataset_name)
        plot_power_iter_vs_s(power_iter, all_spectral, title)
    title = "%s: Frobenius norm diff vs n power iteration" % (dataset_name)
    plot_power_iter_vs_s(power_iter, all_frobenius, title)