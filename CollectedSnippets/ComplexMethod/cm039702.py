def test_group_shuffle_split():
    for groups_i in test_groups:
        X = y = np.ones(len(groups_i))
        n_splits = 6
        test_size = 1.0 / 3
        slo = GroupShuffleSplit(n_splits, test_size=test_size, random_state=0)

        # Make sure the repr works
        repr(slo)

        # Test that the length is correct
        assert slo.get_n_splits(X, y, groups=groups_i) == n_splits

        l_unique = np.unique(groups_i)
        l = np.asarray(groups_i)

        for train, test in slo.split(X, y, groups=groups_i):
            # First test: no train group is in the test set and vice versa
            l_train_unique = np.unique(l[train])
            l_test_unique = np.unique(l[test])
            assert not np.any(np.isin(l[train], l_test_unique))
            assert not np.any(np.isin(l[test], l_train_unique))

            # Second test: train and test add up to all the data
            assert l[train].size + l[test].size == l.size

            # Third test: train and test are disjoint
            assert_array_equal(np.intersect1d(train, test), [])

            # Fourth test:
            # unique train and test groups are correct, +- 1 for rounding error
            assert abs(len(l_test_unique) - round(test_size * len(l_unique))) <= 1
            assert (
                abs(len(l_train_unique) - round((1.0 - test_size) * len(l_unique))) <= 1
            )