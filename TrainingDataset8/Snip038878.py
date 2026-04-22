def _get_deltas_that_melt_dataframes(self):
        return [
            lambda df: st._legacy_line_chart(df),
            lambda df: st._legacy_bar_chart(df),
            lambda df: st._legacy_area_chart(df),
        ]