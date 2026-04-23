def test_target_encoding_for_linear_regression(smooth, global_random_seed):
    # Check some expected statistical properties when fitting a linear
    # regression model on target encoded features depending on their relation
    # with that target.

    # In this test, we use the Ridge class with the "lsqr" solver and a little
    # bit of regularization to implement a linear regression model that
    # converges quickly for large `n_samples` and robustly in case of
    # correlated features. Since we will fit this model on a mean centered
    # target, we do not need to fit an intercept and this will help simplify
    # the analysis with respect to the expected coefficients.
    linear_regression = Ridge(alpha=1e-6, solver="lsqr", fit_intercept=False)

    # Construct a random target variable. We need a large number of samples for
    # this test to be stable across all values of the random seed.
    n_samples = 50_000
    rng = np.random.RandomState(global_random_seed)
    y = rng.randn(n_samples)

    # Generate a single informative ordinal feature with medium cardinality.
    # Inject some irreducible noise to make it harder for a multivariate model
    # to identify the informative feature from other pure noise features.
    noise = 0.8 * rng.randn(n_samples)
    n_categories = 100
    X_informative = KBinsDiscretizer(
        n_bins=n_categories,
        encode="ordinal",
        strategy="uniform",
        random_state=rng,
    ).fit_transform((y + noise).reshape(-1, 1))

    # Let's permute the labels to hide the fact that this feature is
    # informative to naive linear regression model trained on the raw ordinal
    # values. As highlighted in the previous test, the target encoding should be
    # invariant to such a permutation.
    permutated_labels = rng.permutation(n_categories)
    X_informative = permutated_labels[X_informative.astype(np.int32)]

    # Generate a shuffled copy of the informative feature to destroy the
    # relationship with the target.
    X_shuffled = rng.permutation(X_informative)

    # Also include a very high cardinality categorical feature that is by
    # itself independent of the target variable: target encoding such a feature
    # without internal cross-validation should cause catastrophic overfitting
    # for the downstream regressor, even with shrinkage. This kind of features
    # typically represents near unique identifiers of samples. In general they
    # should be removed from a machine learning datasets but here we want to
    # study the ability of the default behavior of TargetEncoder to mitigate
    # them automatically.
    X_near_unique_categories = rng.choice(
        int(0.9 * n_samples), size=n_samples, replace=True
    ).reshape(-1, 1)

    # Assemble the dataset and do a train-test split:
    X = np.concatenate(
        [X_informative, X_shuffled, X_near_unique_categories],
        axis=1,
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

    # Let's first check that a linear regression model trained on the raw
    # features underfits because of the meaning-less ordinal encoding of the
    # labels.
    raw_model = linear_regression.fit(X_train, y_train)
    assert raw_model.score(X_train, y_train) < 0.1
    assert raw_model.score(X_test, y_test) < 0.1

    # Now do the same with target encoding using the internal CV mechanism
    # implemented when using fit_transform.
    cv = KFold(shuffle=True, random_state=rng)
    model_with_cv = make_pipeline(
        TargetEncoder(smooth=smooth, cv=cv), linear_regression
    ).fit(X_train, y_train)

    # This model should be able to fit the data well and also generalise to the
    # test data (assuming that the binning is fine-grained enough). The R2
    # scores are not perfect because of the noise injected during the
    # generation of the unique informative feature.
    coef = model_with_cv[-1].coef_
    assert model_with_cv.score(X_train, y_train) > 0.5, coef
    assert model_with_cv.score(X_test, y_test) > 0.5, coef

    # The target encoder recovers the linear relationship with slope 1 between
    # the target encoded unique informative predictor and the target. Since the
    # target encoding of the 2 other features is not informative thanks to the
    # use of internal cross-validation, the multivariate linear regressor
    # assigns a coef of 1 to the first feature and 0 to the other 2.
    assert coef[0] == pytest.approx(1, abs=1e-2)
    assert (np.abs(coef[1:]) < 0.2).all()

    # Let's now disable the internal cross-validation by calling fit and then
    # transform separately on the training set:
    target_encoder = TargetEncoder(smooth=smooth, cv=cv).fit(X_train, y_train)
    X_enc_no_cv_train = target_encoder.transform(X_train)
    X_enc_no_cv_test = target_encoder.transform(X_test)
    model_no_cv = linear_regression.fit(X_enc_no_cv_train, y_train)

    # The linear regression model should always overfit because it assigns
    # too much weight to the extremely high cardinality feature relatively to
    # the informative feature. Note that this is the case even when using
    # the empirical Bayes smoothing which is not enough to prevent such
    # overfitting alone.
    coef = model_no_cv.coef_
    assert model_no_cv.score(X_enc_no_cv_train, y_train) > 0.7, coef
    assert model_no_cv.score(X_enc_no_cv_test, y_test) < 0.5, coef

    # The model overfits because it assigns too much weight to the high
    # cardinality yet non-informative feature instead of the lower
    # cardinality yet informative feature:
    assert abs(coef[0]) < abs(coef[2])