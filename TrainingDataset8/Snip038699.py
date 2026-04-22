def _get_deltas_that_melt_dataframes(self):
        return [
            lambda df: st._arrow_line_chart(df),
            lambda df: st._arrow_bar_chart(df),
            lambda df: st._arrow_area_chart(df),
        ]