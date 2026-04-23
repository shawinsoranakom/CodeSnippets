def _get_named_data_methods(self):
        """DeltaGenerator methods that produce named datasets."""
        # These should always name the desired data "mydata1"
        return [
            lambda df: st._legacy_vega_lite_chart(
                {
                    "mark": "line",
                    "datasets": {"mydata1": df},
                    "data": {"name": "mydata1"},
                    "encoding": {"x": "a", "y": "b"},
                }
            ),
            # TODO: deck_gl_chart
        ]