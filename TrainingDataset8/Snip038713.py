def test_arrow_bar_chart(self):
        """Test st._arrow_bar_chart."""
        df = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])
        EXPECTED_DATAFRAME = pd.DataFrame(
            [[0, "a", 20], [0, "b", 30], [0, "c", 50]],
            index=[0, 1, 2],
            columns=["index", "variable", "value"],
        )

        st._arrow_bar_chart(df)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        chart_spec = json.loads(proto.spec)

        self.assertEqual(chart_spec["mark"], "bar")
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data),
            EXPECTED_DATAFRAME,
        )