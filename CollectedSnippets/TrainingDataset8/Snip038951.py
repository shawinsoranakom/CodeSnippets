def test_default_zoom_level(self):
        """Test that _DEFAULT_ZOOM_LEVEL is set if zoom is not provided and distance is too small."""
        df = pd.DataFrame({"lat": [1], "lon": [1]})
        st.map(df)

        c = json.loads(self.get_delta_from_queue().new_element.deck_gl_json_chart.json)
        self.assertEqual(c.get("initialViewState").get("zoom"), _DEFAULT_ZOOM_LEVEL)