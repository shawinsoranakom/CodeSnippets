def test_altair_chart(self):
        """Test that it can be called with args."""
        df = pd.DataFrame([["A", "B", "C", "D"], [28, 55, 43, 91]], index=["a", "b"]).T
        chart = alt.Chart(df).mark_bar().encode(x="a", y="b")
        EXPECTED_DATAFRAME = pd.DataFrame(
            {
                "a": ["A", "B", "C", "D"],
                "b": [28, 55, 43, 91],
            }
        )

        st._arrow_altair_chart(chart)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart

        self.assertEqual(proto.HasField("data"), False)
        self.assertEqual(len(proto.datasets), 1)
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data), EXPECTED_DATAFRAME
        )

        spec_dict = json.loads(proto.spec)
        self.assertEqual(
            spec_dict["encoding"],
            {
                "y": {"field": "b", "type": "quantitative"},
                "x": {"field": "a", "type": "nominal"},
            },
        )
        self.assertEqual(spec_dict["data"], {"name": proto.datasets[0].name})
        self.assertEqual(spec_dict["mark"], "bar")
        self.assertTrue("encoding" in spec_dict)