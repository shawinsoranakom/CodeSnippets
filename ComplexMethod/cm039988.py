def one_run(n_samples):
    X_train = X_train_[:n_samples]
    X_test = X_test_[:n_samples]
    y_train = y_train_[:n_samples]
    y_test = y_test_[:n_samples]
    if sample_weight is not None:
        sample_weight_train = sample_weight_train_[:n_samples]
    else:
        sample_weight_train = None
    assert X_train.shape[0] == n_samples
    assert X_test.shape[0] == n_samples
    print("Data size: %d samples train, %d samples test." % (n_samples, n_samples))
    print("Fitting a sklearn model...")
    tic = time()
    est = Estimator(
        learning_rate=lr,
        max_iter=n_trees,
        max_bins=max_bins,
        max_leaf_nodes=n_leaf_nodes,
        early_stopping=False,
        random_state=0,
        verbose=0,
    )
    loss = args.loss
    if args.problem == "classification":
        if loss == "default":
            loss = "log_loss"
    else:
        # regression
        if loss == "default":
            loss = "squared_error"
    est.set_params(loss=loss)
    est.fit(X_train, y_train, sample_weight=sample_weight_train)
    sklearn_fit_duration = time() - tic
    tic = time()
    sklearn_score = est.score(X_test, y_test)
    sklearn_score_duration = time() - tic
    print("score: {:.4f}".format(sklearn_score))
    print("fit duration: {:.3f}s,".format(sklearn_fit_duration))
    print("score duration: {:.3f}s,".format(sklearn_score_duration))

    lightgbm_score = None
    lightgbm_fit_duration = None
    lightgbm_score_duration = None
    if args.lightgbm:
        print("Fitting a LightGBM model...")
        lightgbm_est = get_equivalent_estimator(
            est, lib="lightgbm", n_classes=args.n_classes
        )

        tic = time()
        lightgbm_est.fit(X_train, y_train, sample_weight=sample_weight_train)
        lightgbm_fit_duration = time() - tic
        tic = time()
        lightgbm_score = lightgbm_est.score(X_test, y_test)
        lightgbm_score_duration = time() - tic
        print("score: {:.4f}".format(lightgbm_score))
        print("fit duration: {:.3f}s,".format(lightgbm_fit_duration))
        print("score duration: {:.3f}s,".format(lightgbm_score_duration))

    xgb_score = None
    xgb_fit_duration = None
    xgb_score_duration = None
    if args.xgboost:
        print("Fitting an XGBoost model...")
        xgb_est = get_equivalent_estimator(est, lib="xgboost", n_classes=args.n_classes)

        tic = time()
        xgb_est.fit(X_train, y_train, sample_weight=sample_weight_train)
        xgb_fit_duration = time() - tic
        tic = time()
        xgb_score = xgb_est.score(X_test, y_test)
        xgb_score_duration = time() - tic
        print("score: {:.4f}".format(xgb_score))
        print("fit duration: {:.3f}s,".format(xgb_fit_duration))
        print("score duration: {:.3f}s,".format(xgb_score_duration))

    cat_score = None
    cat_fit_duration = None
    cat_score_duration = None
    if args.catboost:
        print("Fitting a CatBoost model...")
        cat_est = get_equivalent_estimator(
            est, lib="catboost", n_classes=args.n_classes
        )

        tic = time()
        cat_est.fit(X_train, y_train, sample_weight=sample_weight_train)
        cat_fit_duration = time() - tic
        tic = time()
        cat_score = cat_est.score(X_test, y_test)
        cat_score_duration = time() - tic
        print("score: {:.4f}".format(cat_score))
        print("fit duration: {:.3f}s,".format(cat_fit_duration))
        print("score duration: {:.3f}s,".format(cat_score_duration))

    return (
        sklearn_score,
        sklearn_fit_duration,
        sklearn_score_duration,
        lightgbm_score,
        lightgbm_fit_duration,
        lightgbm_score_duration,
        xgb_score,
        xgb_fit_duration,
        xgb_score_duration,
        cat_score,
        cat_fit_duration,
        cat_score_duration,
    )