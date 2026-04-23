def test_grower_interaction_constraints():
    """Check that grower respects interaction constraints."""
    n_features = 6
    interaction_cst = [{0, 1}, {1, 2}, {3, 4, 5}]
    n_samples = 10
    n_bins = 6
    root_feature_splits = []

    def get_all_children(node):
        res = []
        if node.is_leaf:
            return res
        for n in [node.left_child, node.right_child]:
            res.append(n)
            res.extend(get_all_children(n))
        return res

    for seed in range(20):
        rng = np.random.RandomState(seed)

        X_binned = rng.randint(
            0, n_bins - 1, size=(n_samples, n_features), dtype=X_BINNED_DTYPE
        )
        X_binned = np.asfortranarray(X_binned)
        gradients = rng.normal(size=n_samples).astype(G_H_DTYPE)
        hessians = np.ones(shape=1, dtype=G_H_DTYPE)

        grower = TreeGrower(
            X_binned,
            gradients,
            hessians,
            n_bins=n_bins,
            min_samples_leaf=1,
            interaction_cst=interaction_cst,
            n_threads=n_threads,
        )
        grower.grow()

        root_feature_idx = grower.root.split_info.feature_idx
        root_feature_splits.append(root_feature_idx)

        feature_idx_to_constraint_set = {
            0: {0, 1},
            1: {0, 1, 2},
            2: {1, 2},
            3: {3, 4, 5},
            4: {3, 4, 5},
            5: {3, 4, 5},
        }

        root_constraint_set = feature_idx_to_constraint_set[root_feature_idx]
        for node in (grower.root.left_child, grower.root.right_child):
            # Root's children's allowed_features must be the root's constraints set.
            assert_array_equal(node.allowed_features, list(root_constraint_set))
        for node in get_all_children(grower.root):
            if node.is_leaf:
                continue
            # Ensure that each node uses a subset of features of its parent node.
            parent_interaction_cst_indices = set(node.interaction_cst_indices)
            right_interactions_cst_indices = set(
                node.right_child.interaction_cst_indices
            )
            left_interactions_cst_indices = set(node.left_child.interaction_cst_indices)

            assert right_interactions_cst_indices.issubset(
                parent_interaction_cst_indices
            )
            assert left_interactions_cst_indices.issubset(
                parent_interaction_cst_indices
            )
            # The features used for split must have been present in the root's
            # constraint set.
            assert node.split_info.feature_idx in root_constraint_set

    # Make sure that every feature is used at least once as split for the root node.
    assert (
        len(set(root_feature_splits))
        == len(set().union(*interaction_cst))
        == n_features
    )