def _validate_output(self, result):
        """
        Ensure that the output of each transformer is 2D. Otherwise
        hstack can raise an error or produce incorrect results.
        """
        names = [
            name
            for name, _, _, _ in self._iter(
                fitted=True,
                column_as_labels=False,
                skip_drop=True,
                skip_empty_columns=True,
            )
        ]
        for Xs, name in zip(result, names):
            if not getattr(Xs, "ndim", 0) == 2 and not hasattr(Xs, "__dataframe__"):
                raise ValueError(
                    "The output of the '{0}' transformer should be 2D (numpy array, "
                    "scipy sparse array, dataframe).".format(name)
                )
        if _get_output_config("transform", self)["dense"] == "pandas":
            return
        try:
            import pandas as pd
        except ImportError:
            return
        for Xs, name in zip(result, names):
            if not is_pandas_df(Xs):
                continue
            for col_name, dtype in Xs.dtypes.to_dict().items():
                if getattr(dtype, "na_value", None) is not pd.NA:
                    continue
                if pd.NA not in Xs[col_name].values:
                    continue
                class_name = self.__class__.__name__
                raise ValueError(
                    f"The output of the '{name}' transformer for column"
                    f" '{col_name}' has dtype {dtype} and uses pandas.NA to"
                    " represent null values. Storing this output in a numpy array"
                    " can cause errors in downstream scikit-learn estimators, and"
                    " inefficiencies. To avoid this problem you can (i)"
                    " store the output in a pandas DataFrame by using"
                    f" {class_name}.set_output(transform='pandas') or (ii) modify"
                    f" the input data or the '{name}' transformer to avoid the"
                    " presence of pandas.NA (for example by using"
                    " pandas.DataFrame.astype)."
                )