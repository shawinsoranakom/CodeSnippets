def test_empty(self):
        """Test st.write from a specific element."""
        placeholder = st.empty()

        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as p:
            placeholder.write("One argument is okay...")

            p.assert_called_once()

        with self.assertRaises(StreamlitAPIException):
            # Also override dg._is_top_level for this test.
            with patch.object(
                st.delta_generator.DeltaGenerator,
                "_is_top_level",
                new_callable=PropertyMock,
            ) as top_level:
                top_level.return_value = False

                placeholder.write("But", "multiple", "args", "should", "fail")