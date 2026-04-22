def test_arrow_chart_with_x_y(self, chart_command: Callable, altair_type: str):
        """Test x/y-support for built-in charts."""
        df = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])
        EXPECTED_DATAFRAME = pd.DataFrame([[20, 30]], columns=["a", "b"])

        chart_command(df, x="a", y="b")

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        chart_spec = json.loads(proto.spec)

        self.assertEqual(chart_spec["mark"], altair_type)
        self.assertEqual(chart_spec["encoding"]["x"]["field"], "a")
        self.assertEqual(chart_spec["encoding"]["y"]["field"], "b")
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data),
            EXPECTED_DATAFRAME,
        )