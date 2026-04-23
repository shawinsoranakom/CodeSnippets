def assert_nd_reg_tree_children_monotonic_bounded(tree_, monotonic_cst):
    upper_bound = np.full(tree_.node_count, np.inf)
    lower_bound = np.full(tree_.node_count, -np.inf)
    for i in range(tree_.node_count):
        feature = tree_.feature[i]
        node_value = tree_.value[i][0][0]  # unpack value from nx1x1 array
        # While building the tree, the computed middle value is slightly
        # different from the average of the siblings values, because
        # sum_right / weighted_n_right
        # is slightly different from the value of the right sibling.
        # This can cause a discrepancy up to numerical noise when clipping,
        # which is resolved by comparing with some loss of precision.
        assert np.float32(node_value) <= np.float32(upper_bound[i])
        assert np.float32(node_value) >= np.float32(lower_bound[i])

        if feature < 0:
            # Leaf: nothing to do
            continue

        # Split node: check and update bounds for the children.
        i_left = tree_.children_left[i]
        i_right = tree_.children_right[i]
        # unpack value from nx1x1 array
        middle_value = (tree_.value[i_left][0][0] + tree_.value[i_right][0][0]) / 2

        if monotonic_cst[feature] == 0:
            # Feature without monotonicity constraint: propagate bounds
            # down the tree to both children.
            # Otherwise, with 2 features and a monotonic increase constraint
            # (encoded by +1) on feature 0, the following tree can be accepted,
            # although it does not respect the monotonic increase constraint:
            #
            #                      X[0] <= 0
            #                      value = 100
            #                     /            \
            #          X[0] <= -1                X[1] <= 0
            #          value = 50                value = 150
            #        /            \             /            \
            #    leaf           leaf           leaf          leaf
            #    value = 25     value = 75     value = 50    value = 250

            lower_bound[i_left] = lower_bound[i]
            upper_bound[i_left] = upper_bound[i]
            lower_bound[i_right] = lower_bound[i]
            upper_bound[i_right] = upper_bound[i]

        elif monotonic_cst[feature] == 1:
            # Feature with constraint: check monotonicity
            assert tree_.value[i_left] <= tree_.value[i_right]

            # Propagate bounds down the tree to both children.
            lower_bound[i_left] = lower_bound[i]
            upper_bound[i_left] = middle_value
            lower_bound[i_right] = middle_value
            upper_bound[i_right] = upper_bound[i]

        elif monotonic_cst[feature] == -1:
            # Feature with constraint: check monotonicity
            assert tree_.value[i_left] >= tree_.value[i_right]

            # Update and propagate bounds down the tree to both children.
            lower_bound[i_left] = middle_value
            upper_bound[i_left] = upper_bound[i]
            lower_bound[i_right] = lower_bound[i]
            upper_bound[i_right] = middle_value

        else:  # pragma: no cover
            raise ValueError(f"monotonic_cst[{feature}]={monotonic_cst[feature]}")