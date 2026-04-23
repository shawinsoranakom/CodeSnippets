def test_robustness_to_high_cardinality_noisy_feature(n_jobs, max_samples, seed=42):
    # Permutation variable importance should not be affected by the high
    # cardinality bias of traditional feature importances, especially when
    # computed on a held-out test set:
    rng = np.random.RandomState(seed)
    n_repeats = 5
    n_samples = 1000
    n_classes = 5
    n_informative_features = 2
    n_noise_features = 1
    n_features = n_informative_features + n_noise_features

    # Generate a multiclass classification dataset and a set of informative
    # binary features that can be used to predict some classes of y exactly
    # while leaving some classes unexplained to make the problem harder.
    classes = np.arange(n_classes)
    y = rng.choice(classes, size=n_samples)
    X = np.hstack([(y == c).reshape(-1, 1) for c in classes[:n_informative_features]])
    X = X.astype(np.float32)

    # Not all target classes are explained by the binary class indicator
    # features:
    assert n_informative_features < n_classes

    # Add 10 other noisy features with high cardinality (numerical) values
    # that can be used to overfit the training data.
    X = np.concatenate([X, rng.randn(n_samples, n_noise_features)], axis=1)
    assert X.shape == (n_samples, n_features)

    # Split the dataset to be able to evaluate on a held-out test set. The
    # Test size should be large enough for importance measurements to be
    # stable:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.5, random_state=rng
    )
    clf = RandomForestClassifier(n_estimators=5, random_state=rng)
    clf.fit(X_train, y_train)

    # Variable importances computed by impurity decrease on the tree node
    # splits often use the noisy features in splits. This can give misleading
    # impression that high cardinality noisy variables are the most important:
    tree_importances = clf.feature_importances_
    informative_tree_importances = tree_importances[:n_informative_features]
    noisy_tree_importances = tree_importances[n_informative_features:]
    assert informative_tree_importances.max() < noisy_tree_importances.min()

    # Let's check that permutation-based feature importances do not have this
    # problem.
    r = permutation_importance(
        clf,
        X_test,
        y_test,
        n_repeats=n_repeats,
        random_state=rng,
        n_jobs=n_jobs,
        max_samples=max_samples,
    )

    assert r.importances.shape == (X.shape[1], n_repeats)

    # Split the importances between informative and noisy features
    informative_importances = r.importances_mean[:n_informative_features]
    noisy_importances = r.importances_mean[n_informative_features:]

    # Because we do not have a binary variable explaining each target classes,
    # the RF model will have to use the random variable to make some
    # (overfitting) splits (as max_depth is not set). Therefore the noisy
    # variables will be non-zero but with small values oscillating around
    # zero:
    assert max(np.abs(noisy_importances)) > 1e-7
    assert noisy_importances.max() < 0.05

    # The binary features correlated with y should have a higher importance
    # than the high cardinality noisy features.
    # The maximum test accuracy is 2 / 5 == 0.4, each informative feature
    # contributing approximately a bit more than 0.2 of accuracy.
    assert informative_importances.min() > 0.15