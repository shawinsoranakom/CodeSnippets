def _add_prefix_for_feature_names_out(self, transformer_with_feature_names_out):
        """Add prefix for feature names out that includes the transformer names.

        Parameters
        ----------
        transformer_with_feature_names_out : list of tuples of (str, array-like of str)
            The tuple consistent of the transformer's name and its feature names out.

        Returns
        -------
        feature_names_out : ndarray of shape (n_features,), dtype=str
            Transformed feature names.
        """
        feature_names_out_callable = None
        if callable(self.verbose_feature_names_out):
            feature_names_out_callable = self.verbose_feature_names_out
        elif isinstance(self.verbose_feature_names_out, str):
            feature_names_out_callable = partial(
                _feature_names_out_with_str_format,
                str_format=self.verbose_feature_names_out,
            )
        elif self.verbose_feature_names_out is True:
            feature_names_out_callable = partial(
                _feature_names_out_with_str_format,
                str_format="{transformer_name}__{feature_name}",
            )

        if feature_names_out_callable is not None:
            # Prefix the feature names out with the transformers name
            names = list(
                chain.from_iterable(
                    (feature_names_out_callable(name, i) for i in feature_names_out)
                    for name, feature_names_out in transformer_with_feature_names_out
                )
            )
            return np.asarray(names, dtype=object)

        # verbose_feature_names_out is False
        # Check that names are all unique without a prefix
        feature_names_count = Counter(
            chain.from_iterable(s for _, s in transformer_with_feature_names_out)
        )
        top_6_overlap = [
            name for name, count in feature_names_count.most_common(6) if count > 1
        ]
        top_6_overlap.sort()
        if top_6_overlap:
            if len(top_6_overlap) == 6:
                # There are more than 5 overlapping names, we only show the 5
                # of the feature names
                names_repr = str(top_6_overlap[:5])[:-1] + ", ...]"
            else:
                names_repr = str(top_6_overlap)
            raise ValueError(
                f"Output feature names: {names_repr} are not unique. Please set "
                "verbose_feature_names_out=True to add prefixes to feature names"
            )

        return np.concatenate(
            [name for _, name in transformer_with_feature_names_out],
        )