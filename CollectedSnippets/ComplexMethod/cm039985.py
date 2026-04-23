def fit_single(
    solver,
    X,
    y,
    penalty="l2",
    single_target=True,
    C=1,
    max_iter=10,
    skip_slow=False,
    dtype=np.float64,
):
    if skip_slow and solver == "lightning" and penalty == "l1":
        print("skip_slowping l1 logistic regression with solver lightning.")
        return

    print(
        "Solving %s logistic regression with penalty %s, solver %s."
        % ("binary" if single_target else "multinomial", penalty, solver)
    )

    if solver == "lightning":
        from lightning.classification import SAGAClassifier

    if single_target or solver not in ["sag", "saga"]:
        multi_class = "ovr"
    else:
        multi_class = "multinomial"
    X = X.astype(dtype)
    y = y.astype(dtype)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=42, stratify=y
    )
    n_samples = X_train.shape[0]
    n_classes = np.unique(y_train).shape[0]
    test_scores = [1]
    train_scores = [1]
    accuracies = [1 / n_classes]
    times = [0]

    if penalty == "l2":
        l1_ratio = 0
        alpha = 1.0 / (C * n_samples)
        beta = 0
        lightning_penalty = None
    else:
        l1_ratio = 1
        alpha = 0.0
        beta = 1.0 / (C * n_samples)
        lightning_penalty = "l1"

    for this_max_iter in range(1, max_iter + 1, 2):
        print(
            "[%s, %s, %s] Max iter: %s"
            % (
                "binary" if single_target else "multinomial",
                penalty,
                solver,
                this_max_iter,
            )
        )
        if solver == "lightning":
            lr = SAGAClassifier(
                loss="log",
                alpha=alpha,
                beta=beta,
                penalty=lightning_penalty,
                tol=-1,
                max_iter=this_max_iter,
            )
        else:
            lr = LogisticRegression(
                solver=solver,
                C=C,
                l1_ratio=l1_ratio,
                fit_intercept=False,
                tol=0,
                max_iter=this_max_iter,
                random_state=42,
            )
            if multi_class == "ovr":
                lr = OneVsRestClassifier(lr)

        # Makes cpu cache even for all fit calls
        X_train.max()
        t0 = time.clock()

        lr.fit(X_train, y_train)
        train_time = time.clock() - t0

        scores = []
        for X, y in [(X_train, y_train), (X_test, y_test)]:
            try:
                y_proba = lr.predict_proba(X)
            except NotImplementedError:
                # Lightning predict_proba is not implemented for n_classes > 2
                y_proba = _predict_proba(lr, X)
            if isinstance(lr, OneVsRestClassifier):
                coef = np.concatenate([est.coef_ for est in lr.estimators_])
            else:
                coef = lr.coef_
            score = log_loss(y, y_proba, normalize=False) / n_samples
            score += 0.5 * alpha * np.sum(coef**2) + beta * np.sum(np.abs(coef))
            scores.append(score)
        train_score, test_score = tuple(scores)

        y_pred = lr.predict(X_test)
        accuracy = np.sum(y_pred == y_test) / y_test.shape[0]
        test_scores.append(test_score)
        train_scores.append(train_score)
        accuracies.append(accuracy)
        times.append(train_time)
    return lr, times, train_scores, test_scores, accuracies