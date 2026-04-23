def test_st_arrow_bar_chart(self):
        """Test st._arrow_bar_chart."""
        from streamlit.type_util import bytes_to_data_frame

        df = pd.DataFrame([[10, 20, 30]], columns=["a", "b", "c"])
        EXPECTED_DATAFRAME = pd.DataFrame(
            [[0, "a", 10], [0, "b", 20], [0, "c", 30]],
            index=[0, 1, 2],
            columns=["index", "variable", "value"],
        )

        st._arrow_bar_chart(df, width=640, height=480)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        chart_spec = json.loads(proto.spec)

        self.assertEqual(chart_spec["mark"], "bar")
        self.assertEqual(chart_spec["width"], 640)
        self.assertEqual(chart_spec["height"], 480)
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data),
            EXPECTED_DATAFRAME,
        )