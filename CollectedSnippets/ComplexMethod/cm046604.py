def _validator(df):
        import pandas as pd  # imported lazily for local callable runtime

        row_count = int(len(df.index))
        if row_count == 0:
            return pd.DataFrame({"is_valid": []})

        code_column = str(df.columns[0]) if len(df.columns) > 0 else ""
        code_values = (
            ["" for _ in range(row_count)]
            if not code_column
            else [
                "" if value is None else str(value)
                for value in df[code_column].tolist()
            ]
        )

        results = _run_oxc_batch(
            node_lang = node_lang,
            validation_mode = mode,
            code_shape = normalized_code_shape,
            code_values = code_values,
        )
        if len(results) != row_count:
            results = _fallback_results(
                row_count,
                "OXC validator returned mismatched result size.",
            )
        return pd.DataFrame(results)