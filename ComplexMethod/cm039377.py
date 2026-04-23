def check_min_weight_fraction_leaf(name, datasets, sparse_container=None):
    """Test if leaves contain at least min_weight_fraction_leaf of the
    training set"""
    X = DATASETS[datasets]["X"].astype(np.float32)
    if sparse_container is not None:
        X = sparse_container(X)
    y = DATASETS[datasets]["y"]

    weights = rng.rand(X.shape[0])
    total_weight = np.sum(weights)

    TreeEstimator = ALL_TREES[name]

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 6)):
        est = TreeEstimator(
            min_weight_fraction_leaf=frac, max_leaf_nodes=max_leaf_nodes, random_state=0
        )
        est.fit(X, y, sample_weight=weights)

        if sparse_container is not None:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out, weights=weights)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert np.min(leaf_weights) >= total_weight * est.min_weight_fraction_leaf, (
            "Failed with {0} min_weight_fraction_leaf={1}".format(
                name, est.min_weight_fraction_leaf
            )
        )

    # test case with no weights passed in
    total_weight = X.shape[0]

    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 6)):
        est = TreeEstimator(
            min_weight_fraction_leaf=frac, max_leaf_nodes=max_leaf_nodes, random_state=0
        )
        est.fit(X, y)

        if sparse_container is not None:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert np.min(leaf_weights) >= total_weight * est.min_weight_fraction_leaf, (
            "Failed with {0} min_weight_fraction_leaf={1}".format(
                name, est.min_weight_fraction_leaf
            )
        )