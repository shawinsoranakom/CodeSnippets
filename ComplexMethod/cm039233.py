def _sk_visual_block_(self):
        # We can find remainder and its column only when it's fitted
        if hasattr(self, "transformers_"):
            transformers = (
                self.transformers_[:-1]
                if self.transformers_ and self.transformers_[-1][0] == "remainder"
                else self.transformers_
            )

            # Add remainder back to fitted transformers if remainder is not drop
            # and if there are remainder columns to display
            remainder_columns = self._remainder[2]
            if self.remainder != "drop" and remainder_columns:
                has_numeric_columns = not all(
                    isinstance(col, str) for col in remainder_columns
                )
                # Convert indices to column names when feature names are available
                if hasattr(self, "feature_names_in_") and has_numeric_columns:
                    remainder_columns = self.feature_names_in_[
                        remainder_columns
                    ].tolist()
                # get the fitted remainder function so we can access its methods to
                # build the display in utils._repr_html.estimator.py
                remainder_transformer = self.transformers_[-1][1]

                transformers = chain(
                    transformers,
                    [("remainder", remainder_transformer, remainder_columns)],
                )
        else:  # not fitted
            if self.remainder != "drop":
                transformers = chain(
                    self.transformers, [("remainder", self.remainder, [])]
                )
            else:
                transformers = self.transformers
        names, transformers, name_details = zip(*transformers)

        return _VisualBlock(
            "parallel", transformers, names=names, name_details=name_details
        )