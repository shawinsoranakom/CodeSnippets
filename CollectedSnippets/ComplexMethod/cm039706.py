def test_group_kfold(kfold, shuffle, global_random_seed):
    rng = np.random.RandomState(global_random_seed)

    # Parameters of the test
    n_groups = 15
    n_samples = 1000
    n_splits = 5

    X = y = np.ones(n_samples)

    # Construct the test data
    tolerance = 0.05 * n_samples  # 5 percent error allowed
    groups = rng.randint(0, n_groups, n_samples)

    ideal_n_groups_per_fold = n_samples // n_splits

    len(np.unique(groups))
    # Get the test fold indices from the test set indices of each fold
    folds = np.zeros(n_samples)
    random_state = None if not shuffle else global_random_seed
    lkf = kfold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    for i, (_, test) in enumerate(lkf.split(X, y, groups)):
        folds[test] = i

    # Check that folds have approximately the same size
    assert len(folds) == len(groups)
    for i in np.unique(folds):
        assert tolerance >= abs(sum(folds == i) - ideal_n_groups_per_fold)

    # Check that each group appears only in 1 fold
    for group in np.unique(groups):
        assert len(np.unique(folds[groups == group])) == 1

    # Check that no group is on both sides of the split
    groups = np.asarray(groups, dtype=object)
    for train, test in lkf.split(X, y, groups):
        assert len(np.intersect1d(groups[train], groups[test])) == 0

    # Construct the test data
    groups = np.array(
        [
            "Albert",
            "Jean",
            "Bertrand",
            "Michel",
            "Jean",
            "Francis",
            "Robert",
            "Michel",
            "Rachel",
            "Lois",
            "Michelle",
            "Bernard",
            "Marion",
            "Laura",
            "Jean",
            "Rachel",
            "Franck",
            "John",
            "Gael",
            "Anna",
            "Alix",
            "Robert",
            "Marion",
            "David",
            "Tony",
            "Abel",
            "Becky",
            "Madmood",
            "Cary",
            "Mary",
            "Alexandre",
            "David",
            "Francis",
            "Barack",
            "Abdoul",
            "Rasha",
            "Xi",
            "Silvia",
        ]
    )

    n_groups = len(np.unique(groups))
    n_samples = len(groups)
    n_splits = 5
    tolerance = 0.05 * n_samples  # 5 percent error allowed
    ideal_n_groups_per_fold = n_samples // n_splits

    X = y = np.ones(n_samples)

    # Get the test fold indices from the test set indices of each fold
    folds = np.zeros(n_samples)
    for i, (_, test) in enumerate(lkf.split(X, y, groups)):
        folds[test] = i

    # Check that folds have approximately the same size
    assert len(folds) == len(groups)
    if not shuffle:
        for i in np.unique(folds):
            assert tolerance >= abs(sum(folds == i) - ideal_n_groups_per_fold)

    # Check that each group appears only in 1 fold
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        for group in np.unique(groups):
            assert len(np.unique(folds[groups == group])) == 1

    # Check that no group is on both sides of the split
    groups = np.asarray(groups, dtype=object)
    for train, test in lkf.split(X, y, groups):
        assert len(np.intersect1d(groups[train], groups[test])) == 0

    # groups can also be a list
    # use a new instance for reproducibility when shuffle=True
    lkf_copy = kfold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    cv_iter = list(lkf.split(X, y, groups.tolist()))
    for (train1, test1), (train2, test2) in zip(lkf_copy.split(X, y, groups), cv_iter):
        assert_array_equal(train1, train2)
        assert_array_equal(test1, test2)

    # Should fail if there are more folds than groups
    groups = np.array([1, 1, 1, 2, 2])
    X = y = np.ones(len(groups))
    with pytest.raises(ValueError, match="Cannot have number of splits.*greater"):
        next(kfold(n_splits=3).split(X, y, groups))