def get_feature_names_out(self, input_features=None):
        """Get output feature names for transformation.

        Parameters
        ----------
        input_features : array-like of str or None, default=None
            Not used, present here for API consistency by convention.

        Returns
        -------
        feature_names_out : ndarray of str objects
            Transformed feature names.
        """
        check_is_fitted(self, "n_features_in_")
        if self.voting == "soft" and not self.flatten_transform:
            raise ValueError(
                "get_feature_names_out is not supported when `voting='soft'` and "
                "`flatten_transform=False`"
            )

        _check_feature_names_in(self, input_features, generate_names=False)
        class_name = self.__class__.__name__.lower()

        active_names = [name for name, est in self.estimators if est != "drop"]

        if self.voting == "hard":
            return np.asarray(
                [f"{class_name}_{name}" for name in active_names], dtype=object
            )

        # voting == "soft"
        n_classes = len(self.classes_)
        names_out = [
            f"{class_name}_{name}{i}" for name in active_names for i in range(n_classes)
        ]
        return np.asarray(names_out, dtype=object)