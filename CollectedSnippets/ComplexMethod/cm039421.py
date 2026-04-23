def _validate_y_class_weight(self, y, sample_weight):
        check_classification_targets(y)

        y_original = np.copy(y)
        self.classes_ = []
        self.n_classes_ = []

        y_store_unique_indices = np.zeros(y.shape, dtype=int)
        for k in range(self.n_outputs_):
            classes_k, y_store_unique_indices[:, k] = np.unique(
                y[:, k], return_inverse=True
            )
            self.classes_.append(classes_k)
            self.n_classes_.append(classes_k.shape[0])
        y = y_store_unique_indices

        if self.class_weight is None:
            return y, None

        # User defined class_weight (dict or list)
        if isinstance(self.class_weight, (dict, list)):
            expanded_class_weight = compute_sample_weight(self.class_weight, y_original)
            return y, expanded_class_weight

        # Checking class_weight options
        valid_presets = ("balanced", "balanced_subsample")
        if self.class_weight not in valid_presets:
            raise ValueError(
                "Valid presets for class_weight include "
                '"balanced" and "balanced_subsample".'
                'Given "%s".' % self.class_weight
            )
        if self.warm_start:
            warn(
                'class_weight presets "balanced" or '
                '"balanced_subsample" are '
                "not recommended for warm_start if the fitted data "
                "differs from the full dataset. In order to use "
                '"balanced" weights, use compute_class_weight '
                '("balanced", classes, y). In place of y you can use '
                "a large enough sample of the full training set "
                "target to properly estimate the class frequency "
                "distributions. Pass the resulting weights as the "
                "class_weight parameter."
            )

        # "balanced_subsample" option with subsampling (bootstrap=True)
        if self.class_weight == "balanced_subsample" and self.bootstrap:
            # class_weight will be computed on the bootstrap sample
            return y, None

        # Computing class_weight (dict or list) for the "balanced" option.
        # The "balanced_subsample" option without subsampling (bootstrap=False)
        # is equivalent to the "balanced" option.
        class_weight = []
        for k in range(self.n_outputs_):
            class_weight_k_vect = compute_class_weight(
                "balanced",
                classes=self.classes_[k],
                y=y_original[:, k],
                sample_weight=sample_weight,
            )
            class_weight_k = {
                key: val for (key, val) in zip(self.classes_[k], class_weight_k_vect)
            }
            class_weight.append(class_weight_k)
        if self.n_outputs_ == 1:
            class_weight = class_weight[0]

        expanded_class_weight = compute_sample_weight(class_weight, y_original)
        return y, expanded_class_weight