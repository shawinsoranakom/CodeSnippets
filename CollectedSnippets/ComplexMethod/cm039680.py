def _iter_indices(self, X, y, groups=None):
        n_samples = _num_samples(X)
        y = check_array(y, input_name="y", ensure_2d=False, dtype=None)
        n_train, n_test = _validate_shuffle_split(
            n_samples,
            self.test_size,
            self.train_size,
            default_test_size=self._default_test_size,
        )

        # Convert to numpy as not all operations are supported by the Array API.
        # `y` is probably never a very large array, which means that converting it
        # should be cheap
        xp, _ = get_namespace(y)
        y = move_to(y, xp=np, device="cpu")

        if y.ndim == 2:
            # for multi-label y, map each distinct row to a string repr
            # using join because str(row) uses an ellipsis if len(row) > 1000
            y = np.array([" ".join(row.astype("str")) for row in y])

        classes, y_indices, class_counts = np.unique(
            y, return_inverse=True, return_counts=True
        )
        n_classes = classes.shape[0]

        if np.min(class_counts) < 2:
            too_few_classes = classes[class_counts < 2].tolist()
            raise ValueError(
                "The least populated classes in y have only 1"
                " member, which is too few. The minimum"
                " number of groups for any class cannot"
                " be less than 2. Classes with too few"
                " members are: %s" % (too_few_classes)
            )

        if n_train < n_classes:
            raise ValueError(
                "The train_size = %d should be greater or "
                "equal to the number of classes = %d" % (n_train, n_classes)
            )
        if n_test < n_classes:
            raise ValueError(
                "The test_size = %d should be greater or "
                "equal to the number of classes = %d" % (n_test, n_classes)
            )

        # Find the sorted list of instances for each class:
        # (np.unique above performs a sort, so code is O(n logn) already)
        class_indices = np.split(
            np.argsort(y_indices, kind="stable"), np.cumsum(class_counts)[:-1]
        )

        rng = check_random_state(self.random_state)

        for _ in range(self.n_splits):
            # if there are ties in the class-counts, we want
            # to make sure to break them anew in each iteration
            n_i = _approximate_mode(class_counts, n_train, rng)
            class_counts_remaining = class_counts - n_i
            t_i = _approximate_mode(class_counts_remaining, n_test, rng)

            train = []
            test = []

            for i in range(n_classes):
                permutation = rng.permutation(class_counts[i])
                perm_indices_class_i = class_indices[i].take(permutation, mode="clip")

                train.extend(perm_indices_class_i[: n_i[i]])
                test.extend(perm_indices_class_i[n_i[i] : n_i[i] + t_i[i]])

            train = rng.permutation(train)
            test = rng.permutation(test)

            yield train, test