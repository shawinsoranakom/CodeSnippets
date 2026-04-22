def test_arrow_line_chart_with_generic_index(self):
        """Test st._arrow_line_chart with a generic index."""
        df = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])
        df.set_index("a", inplace=True)
        EXPECTED_DATAFRAME = pd.DataFrame(
            [[20, "b", 30], [20, "c", 50]],
            index=[0, 1],
            columns=["a", "variable", "value"],
        )

        st._arrow_line_chart(df)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        chart_spec = json.loads(proto.spec)
        self.assertEqual(chart_spec["mark"], "line")
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data),
            EXPECTED_DATAFRAME,
        )