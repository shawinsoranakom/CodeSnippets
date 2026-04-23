def merge_dataframes(self) -> DataFrame:
        """Merge two DataFrames based on a common column (join operation).

        Uses explicit left_dataframe and right_dataframe inputs to give the user
        deterministic control over which DataFrame is primary (left) and which
        is secondary (right) in the merge.
        """
        left_df = getattr(self, "left_dataframe", None)
        right_df = getattr(self, "right_dataframe", None)

        if left_df is None:
            return DataFrame()

        if right_df is None:
            return left_df.copy()

        df_left = left_df.copy()
        df_right = right_df.copy()

        merge_on = getattr(self, "merge_on_column", None)
        merge_how = getattr(self, "merge_how", "inner")

        if merge_on:
            if merge_on not in df_left.columns:
                msg = f"Column '{merge_on}' not found in left DataFrame. Available: {list(df_left.columns)}"
                raise ValueError(msg)
            if merge_on not in df_right.columns:
                msg = f"Column '{merge_on}' not found in right DataFrame. Available: {list(df_right.columns)}"
                raise ValueError(msg)

            merged = df_left.merge(df_right, on=merge_on, how=merge_how, suffixes=("", "_right"))
        else:
            merged = df_left.merge(df_right, left_index=True, right_index=True, how=merge_how, suffixes=("", "_right"))

        # Combine duplicate columns: use left value if exists, otherwise right value
        cols_to_drop = []
        for col in merged.columns:
            if col.endswith("_right"):
                original_col = col[:-6]  # Remove "_right" suffix
                if original_col in merged.columns:
                    merged[original_col] = merged[original_col].combine_first(merged[col])
                    cols_to_drop.append(col)

        if cols_to_drop:
            merged = merged.drop(columns=cols_to_drop)

        return DataFrame(merged)