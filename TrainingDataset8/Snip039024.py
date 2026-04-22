def test_pydeck_with_tooltip_pydeck_0_8_1(self):
        """Test that pydeck object with tooltip created by pydeck v0.8.1 works."""

        tooltip = {
            "html": "<b>Elevation Value:</b> {elevationValue}",
            "style": {"color": "white"},
        }

        mock_desk = mock.Mock(
            spec=["to_json", "deck_widget"],
            **{
                "to_json.return_value": json.dumps({"layers": []}),
                "deck_widget.tooltip": tooltip,
            },
        )
        st.pydeck_chart(mock_desk)

        el = self.get_delta_from_queue().new_element
        actual = json.loads(el.deck_gl_json_chart.tooltip)

        self.assertEqual(actual, tooltip)