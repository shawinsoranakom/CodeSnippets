def _iter(self, fitted, column_as_labels, skip_drop, skip_empty_columns):
        """
        Generate (name, trans, columns, weight) tuples.


        Parameters
        ----------
        fitted : bool
            If True, use the fitted transformers (``self.transformers_``) to
            iterate through transformers, else use the transformers passed by
            the user (``self.transformers``).

        column_as_labels : bool
            If True, columns are returned as string labels. If False, columns
            are returned as they were given by the user. This can only be True
            if the ``ColumnTransformer`` is already fitted.

        skip_drop : bool
            If True, 'drop' transformers are filtered out.

        skip_empty_columns : bool
            If True, transformers with empty selected columns are filtered out.

        Yields
        ------
        A generator of tuples containing:
            - name : the name of the transformer
            - transformer : the transformer object
            - columns : the columns for that transformer
            - weight : the weight of the transformer
        """
        if fitted:
            transformers = self.transformers_
        else:
            # interleave the validated column specifiers
            transformers = [
                (name, trans, column)
                for (name, trans, _), column in zip(self.transformers, self._columns)
            ]
            # add transformer tuple for remainder
            if self._remainder[2]:
                transformers = chain(transformers, [self._remainder])

        get_weight = (self.transformer_weights or {}).get

        for name, trans, columns in transformers:
            if skip_drop and trans == "drop":
                continue
            if skip_empty_columns and _is_empty_column_selection(columns):
                continue

            if column_as_labels:
                # Convert all columns to using their string labels
                columns_is_scalar = np.isscalar(columns)

                indices = self._transformer_to_input_indices[name]
                columns = self.feature_names_in_[indices]

                if columns_is_scalar:
                    # selection is done with one dimension
                    columns = columns[0]

            yield (name, trans, columns, get_weight(name))