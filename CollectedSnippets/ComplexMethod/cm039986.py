def exp(
    solvers,
    penalty,
    single_target,
    n_samples=30000,
    max_iter=20,
    dataset="rcv1",
    n_jobs=1,
    skip_slow=False,
):
    dtypes_mapping = {
        "float64": np.float64,
        "float32": np.float32,
    }

    if dataset == "rcv1":
        rcv1 = fetch_rcv1()

        lbin = LabelBinarizer()
        lbin.fit(rcv1.target_names)

        X = rcv1.data
        y = rcv1.target
        y = lbin.inverse_transform(y)
        le = LabelEncoder()
        y = le.fit_transform(y)
        if single_target:
            y_n = y.copy()
            y_n[y > 16] = 1
            y_n[y <= 16] = 0
            y = y_n

    elif dataset == "digits":
        X, y = load_digits(return_X_y=True)
        if single_target:
            y_n = y.copy()
            y_n[y < 5] = 1
            y_n[y >= 5] = 0
            y = y_n
    elif dataset == "iris":
        iris = load_iris()
        X, y = iris.data, iris.target
    elif dataset == "20newspaper":
        ng = fetch_20newsgroups_vectorized()
        X = ng.data
        y = ng.target
        if single_target:
            y_n = y.copy()
            y_n[y > 4] = 1
            y_n[y <= 16] = 0
            y = y_n

    X = X[:n_samples]
    y = y[:n_samples]

    out = Parallel(n_jobs=n_jobs, mmap_mode=None)(
        delayed(fit_single)(
            solver,
            X,
            y,
            penalty=penalty,
            single_target=single_target,
            dtype=dtype,
            C=1,
            max_iter=max_iter,
            skip_slow=skip_slow,
        )
        for solver in solvers
        for dtype in dtypes_mapping.values()
    )

    res = []
    idx = 0
    for dtype_name in dtypes_mapping.keys():
        for solver in solvers:
            if not (skip_slow and solver == "lightning" and penalty == "l1"):
                lr, times, train_scores, test_scores, accuracies = out[idx]
                this_res = dict(
                    solver=solver,
                    penalty=penalty,
                    dtype=dtype_name,
                    single_target=single_target,
                    times=times,
                    train_scores=train_scores,
                    test_scores=test_scores,
                    accuracies=accuracies,
                )
                res.append(this_res)
            idx += 1

    with open("bench_saga.json", "w+") as f:
        json.dump(res, f)