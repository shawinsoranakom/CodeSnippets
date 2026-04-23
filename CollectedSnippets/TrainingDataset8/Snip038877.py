def _get_unnamed_data_methods(self):
        """DeltaGenerator methods that do not produce named datasets."""
        return [
            lambda df: st._legacy_dataframe(df),
            lambda df: st._legacy_table(df),
            lambda df: st._legacy_vega_lite_chart(
                df, {"mark": "line", "encoding": {"x": "a", "y": "b"}}
            ),
            # TODO: _legacy_line_chart, _legacy_bar_chart, etc.
        ]