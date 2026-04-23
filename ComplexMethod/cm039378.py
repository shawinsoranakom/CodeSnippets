def check_min_weight_fraction_leaf_with_min_samples_leaf(
    name, datasets, sparse_container=None
):
    """Test the interaction between min_weight_fraction_leaf and
    min_samples_leaf when sample_weights is not provided in fit."""
    X = DATASETS[datasets]["X"].astype(np.float32)
    if sparse_container is not None:
        X = sparse_container(X)
    y = DATASETS[datasets]["y"]

    total_weight = X.shape[0]
    TreeEstimator = ALL_TREES[name]
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 3)):
        # test integer min_samples_leaf
        est = TreeEstimator(
            min_weight_fraction_leaf=frac,
            max_leaf_nodes=max_leaf_nodes,
            min_samples_leaf=5,
            random_state=0,
        )
        est.fit(X, y)

        if sparse_container is not None:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert np.min(leaf_weights) >= max(
            (total_weight * est.min_weight_fraction_leaf), 5
        ), "Failed with {0} min_weight_fraction_leaf={1}, min_samples_leaf={2}".format(
            name, est.min_weight_fraction_leaf, est.min_samples_leaf
        )
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 3)):
        # test float min_samples_leaf
        est = TreeEstimator(
            min_weight_fraction_leaf=frac,
            max_leaf_nodes=max_leaf_nodes,
            min_samples_leaf=0.1,
            random_state=0,
        )
        est.fit(X, y)

        if sparse_container is not None:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert np.min(leaf_weights) >= max(
            (total_weight * est.min_weight_fraction_leaf),
            (total_weight * est.min_samples_leaf),
        ), "Failed with {0} min_weight_fraction_leaf={1}, min_samples_leaf={2}".format(
            name, est.min_weight_fraction_leaf, est.min_samples_leaf
        )