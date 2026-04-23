def test_distribution():
    rng = check_random_state(12321)

    # Single variable with 4 values
    X = rng.randint(0, 4, size=(1000, 1))
    y = rng.rand(1000)
    n_trees = 500

    reg = ExtraTreesRegressor(n_estimators=n_trees, random_state=42).fit(X, y)

    uniques = defaultdict(int)
    for tree in reg.estimators_:
        tree = "".join(
            ("%d,%d/" % (f, int(t)) if f >= 0 else "-")
            for f, t in zip(tree.tree_.feature, tree.tree_.threshold)
        )

        uniques[tree] += 1

    uniques = sorted([(1.0 * count / n_trees, tree) for tree, count in uniques.items()])

    # On a single variable problem where X_0 has 4 equiprobable values, there
    # are 5 ways to build a random tree. The more compact (0,1/0,0/--0,2/--) of
    # them has probability 1/3 while the 4 others have probability 1/6.

    assert len(uniques) == 5
    assert 0.20 > uniques[0][0]  # Rough approximation of 1/6.
    assert 0.20 > uniques[1][0]
    assert 0.20 > uniques[2][0]
    assert 0.20 > uniques[3][0]
    assert uniques[4][0] > 0.3
    assert uniques[4][1] == "0,1/0,0/--0,2/--"

    # Two variables, one with 2 values, one with 3 values
    X = np.empty((1000, 2))
    X[:, 0] = np.random.randint(0, 2, 1000)
    X[:, 1] = np.random.randint(0, 3, 1000)
    y = rng.rand(1000)

    reg = ExtraTreesRegressor(max_features=1, random_state=1).fit(X, y)

    uniques = defaultdict(int)
    for tree in reg.estimators_:
        tree = "".join(
            ("%d,%d/" % (f, int(t)) if f >= 0 else "-")
            for f, t in zip(tree.tree_.feature, tree.tree_.threshold)
        )

        uniques[tree] += 1

    uniques = [(count, tree) for tree, count in uniques.items()]
    assert len(uniques) == 8