def bench_a(X, dataset_name, power_iter, n_oversamples, n_comps):
    all_time = defaultdict(list)
    if enable_spectral_norm:
        all_spectral = defaultdict(list)
        X_spectral_norm = norm_diff(X, norm=2, msg=False, random_state=0)
    all_frobenius = defaultdict(list)
    X_fro_norm = norm_diff(X, norm="fro", msg=False)

    for pi in power_iter:
        for pm in ["none", "LU", "QR"]:
            print("n_iter = %d on sklearn - %s" % (pi, pm))
            U, s, V, time = svd_timing(
                X,
                n_comps,
                n_iter=pi,
                power_iteration_normalizer=pm,
                n_oversamples=n_oversamples,
            )
            label = "sklearn - %s" % pm
            all_time[label].append(time)
            if enable_spectral_norm:
                A = U.dot(np.diag(s).dot(V))
                all_spectral[label].append(
                    norm_diff(X - A, norm=2, random_state=0) / X_spectral_norm
                )
            f = scalable_frobenius_norm_discrepancy(X, U, s, V)
            all_frobenius[label].append(f / X_fro_norm)

        if fbpca_available:
            print("n_iter = %d on fbca" % (pi))
            U, s, V, time = svd_timing(
                X,
                n_comps,
                n_iter=pi,
                power_iteration_normalizer=pm,
                n_oversamples=n_oversamples,
                method="fbpca",
            )
            label = "fbpca"
            all_time[label].append(time)
            if enable_spectral_norm:
                A = U.dot(np.diag(s).dot(V))
                all_spectral[label].append(
                    norm_diff(X - A, norm=2, random_state=0) / X_spectral_norm
                )
            f = scalable_frobenius_norm_discrepancy(X, U, s, V)
            all_frobenius[label].append(f / X_fro_norm)

    if enable_spectral_norm:
        title = "%s: spectral norm diff vs running time" % (dataset_name)
        plot_time_vs_s(all_time, all_spectral, power_iter, title)
    title = "%s: Frobenius norm diff vs running time" % (dataset_name)
    plot_time_vs_s(all_time, all_frobenius, power_iter, title)