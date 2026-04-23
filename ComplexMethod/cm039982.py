def bench_c(datasets, n_comps):
    all_time = defaultdict(list)
    if enable_spectral_norm:
        all_spectral = defaultdict(list)
    all_frobenius = defaultdict(list)

    for dataset_name in datasets:
        X = get_data(dataset_name)
        if X is None:
            continue

        if enable_spectral_norm:
            X_spectral_norm = norm_diff(X, norm=2, msg=False, random_state=0)
        X_fro_norm = norm_diff(X, norm="fro", msg=False)
        n_comps = np.minimum(n_comps, np.min(X.shape))

        label = "sklearn"
        print("%s %d x %d - %s" % (dataset_name, X.shape[0], X.shape[1], label))
        U, s, V, time = svd_timing(X, n_comps, n_iter=2, n_oversamples=10, method=label)

        all_time[label].append(time)
        if enable_spectral_norm:
            A = U.dot(np.diag(s).dot(V))
            all_spectral[label].append(
                norm_diff(X - A, norm=2, random_state=0) / X_spectral_norm
            )
        f = scalable_frobenius_norm_discrepancy(X, U, s, V)
        all_frobenius[label].append(f / X_fro_norm)

        if fbpca_available:
            label = "fbpca"
            print("%s %d x %d - %s" % (dataset_name, X.shape[0], X.shape[1], label))
            U, s, V, time = svd_timing(
                X, n_comps, n_iter=2, n_oversamples=2, method=label
            )
            all_time[label].append(time)
            if enable_spectral_norm:
                A = U.dot(np.diag(s).dot(V))
                all_spectral[label].append(
                    norm_diff(X - A, norm=2, random_state=0) / X_spectral_norm
                )
            f = scalable_frobenius_norm_discrepancy(X, U, s, V)
            all_frobenius[label].append(f / X_fro_norm)

    if len(all_time) == 0:
        raise ValueError("No tests ran. Aborting.")

    if enable_spectral_norm:
        title = "normalized spectral norm diff vs running time"
        scatter_time_vs_s(all_time, all_spectral, datasets, title)
    title = "normalized Frobenius norm diff vs running time"
    scatter_time_vs_s(all_time, all_frobenius, datasets, title)