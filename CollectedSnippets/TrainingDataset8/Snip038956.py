def test_unevaluated_snowpark_dataframe(self):
        """Test st.map with unevaluated Snowpark DataFrame"""
        mocked_snowpark_dataframe = MockedSnowparkDataFrame(
            is_map=True, num_of_rows=50000
        )
        st.map(mocked_snowpark_dataframe)

        c = json.loads(self.get_delta_from_queue().new_element.deck_gl_json_chart.json)

        self.assertIsNotNone(c.get("initialViewState"))
        self.assertIsNotNone(c.get("layers"))
        self.assertIsNone(c.get("mapStyle"))
        self.assertEqual(len(c.get("layers")), 1)
        self.assertEqual(c.get("initialViewState").get("pitch"), 0)
        self.assertEqual(c.get("layers")[0].get("@@type"), "ScatterplotLayer")

        """Check if map data was cut to 10k rows"""
        self.assertEqual(len(c["layers"][0]["data"]), 10000)