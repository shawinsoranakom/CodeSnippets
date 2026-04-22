def test_altair_chart(self, is_type):
        """Test st.write with altair_chart."""
        is_type.side_effect = make_is_type_mock(type_util._ALTAIR_RE)

        class FakeChart(object):
            pass

        with patch("streamlit.delta_generator.DeltaGenerator.altair_chart") as p:
            st.write(FakeChart())

            p.assert_called_once()