def test_pyspark_dataframe(self):
        """Test st.map with pyspark.sql.DataFrame"""
        pyspark_map_dataframe = (
            pyspark_mocks.create_pyspark_dataframe_with_mocked_map_data()
        )
        st.map(pyspark_map_dataframe)

        c = json.loads(self.get_delta_from_queue().new_element.deck_gl_json_chart.json)

        self.assertIsNotNone(c.get("initialViewState"))
        self.assertIsNotNone(c.get("layers"))
        self.assertIsNone(c.get("mapStyle"))
        self.assertEqual(len(c.get("layers")), 1)
        self.assertEqual(c.get("initialViewState").get("pitch"), 0)
        self.assertEqual(c.get("layers")[0].get("@@type"), "ScatterplotLayer")

        """Check if map data has 5 rows"""
        self.assertEqual(len(c["layers"][0]["data"]), 5)