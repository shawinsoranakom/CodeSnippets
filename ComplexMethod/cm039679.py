def _iter_test_indices(self, X, y, groups):
        # Implementation is based on this kaggle kernel:
        # https://www.kaggle.com/jakubwasikowski/stratified-group-k-fold-cross-validation
        # and is a subject to Apache 2.0 License. You may obtain a copy of the
        # License at http://www.apache.org/licenses/LICENSE-2.0
        # Changelist:
        # - Refactored function to a class following scikit-learn KFold
        #   interface.
        # - Added heuristic for assigning group to the least populated fold in
        #   cases when all other criteria are equal
        # - Swtch from using python ``Counter`` to ``np.unique`` to get class
        #   distribution
        # - Added scikit-learn checks for input: checking that target is binary
        #   or multiclass, checking passed random state, checking that number
        #   of splits is less than number of members in each class, checking
        #   that least populated class has more members than there are splits.
        rng = check_random_state(self.random_state)
        y = np.asarray(y)
        type_of_target_y = type_of_target(y)
        allowed_target_types = ("binary", "multiclass")
        if type_of_target_y not in allowed_target_types:
            raise ValueError(
                "Supported target types are: {}. Got {!r} instead.".format(
                    allowed_target_types, type_of_target_y
                )
            )

        y = column_or_1d(y)
        _, y_inv, y_cnt = np.unique(y, return_inverse=True, return_counts=True)
        if np.all(self.n_splits > y_cnt):
            raise ValueError(
                "n_splits=%d cannot be greater than the"
                " number of members in each class." % (self.n_splits)
            )
        n_smallest_class = np.min(y_cnt)
        if self.n_splits > n_smallest_class:
            warnings.warn(
                "The least populated class in y has only %d"
                " members, which is less than n_splits=%d."
                % (n_smallest_class, self.n_splits),
                UserWarning,
            )
        n_classes = len(y_cnt)

        _, groups_inv, groups_cnt = np.unique(
            groups, return_inverse=True, return_counts=True
        )
        n_groups = len(groups_cnt)

        if self.n_splits > n_groups:
            raise ValueError(
                f"Cannot have number of splits n_splits={self.n_splits} greater"
                f" than the number of groups: {n_groups}."
            )

        y_counts_per_group = np.zeros((len(groups_cnt), n_classes))
        for class_idx, group_idx in zip(y_inv, groups_inv):
            y_counts_per_group[group_idx, class_idx] += 1

        y_counts_per_fold = np.zeros((self.n_splits, n_classes))
        groups_per_fold = defaultdict(set)

        if self.shuffle:
            perm = np.arange(len(groups_cnt))
            rng.shuffle(perm)
            y_counts_per_group = y_counts_per_group[perm]
            inv_perm = np.empty_like(perm)
            inv_perm[perm] = np.arange(perm.size)
            groups_inv = inv_perm[groups_inv]

        # Stable sort to keep shuffled order for groups with the same
        # class distribution variance
        sorted_groups_idx = np.argsort(
            -np.std(y_counts_per_group, axis=1), kind="stable"
        )

        for group_idx in sorted_groups_idx:
            group_y_counts = y_counts_per_group[group_idx]
            best_fold = self._find_best_fold(
                y_counts_per_fold=y_counts_per_fold,
                y_cnt=y_cnt,
                group_y_counts=group_y_counts,
            )
            y_counts_per_fold[best_fold] += group_y_counts
            groups_per_fold[best_fold].add(group_idx)

        for i in range(self.n_splits):
            test_indices = [
                idx
                for idx, group_idx in enumerate(groups_inv)
                if group_idx in groups_per_fold[i]
            ]
            yield test_indices