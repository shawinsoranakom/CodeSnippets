def test_basic(self):
        """Test that it can be called with lat/lon."""
        st.map(df1)

        c = json.loads(self.get_delta_from_queue().new_element.deck_gl_json_chart.json)

        self.assertIsNotNone(c.get("initialViewState"))
        self.assertIsNotNone(c.get("layers"))
        self.assertIsNone(c.get("mapStyle"))
        self.assertEqual(len(c.get("layers")), 1)
        self.assertEqual(c.get("initialViewState").get("latitude"), 2.5)
        self.assertEqual(c.get("initialViewState").get("longitude"), 25)
        self.assertEqual(c.get("initialViewState").get("zoom"), 3)
        self.assertEqual(c.get("initialViewState").get("pitch"), 0)
        self.assertEqual(c.get("layers")[0].get("@@type"), "ScatterplotLayer")