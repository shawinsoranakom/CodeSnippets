def test_pydeck_with_tooltip_pydeck_0_7_1(self):
        """Test that pydeck object with tooltip created by pydeck v0.7.1 works."""

        tooltip = {
            "html": "<b>Elevation Value:</b> {elevationValue}",
            "style": {"color": "white"},
        }

        mock_desk = mock.Mock(
            spec=["to_json", "_tooltip"],
            **{"to_json.return_value": json.dumps({"layers": []}), "_tooltip": tooltip},
        )
        st.pydeck_chart(mock_desk)

        el = self.get_delta_from_queue().new_element
        actual = json.loads(el.deck_gl_json_chart.tooltip)

        self.assertEqual(actual, tooltip)