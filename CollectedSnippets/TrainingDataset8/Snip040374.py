def test_pyplot(self, is_type):
        """Test st.write with matplotlib."""
        is_type.side_effect = make_is_type_mock("matplotlib.figure.Figure")

        class FakePyplot(object):
            pass

        with patch("streamlit.delta_generator.DeltaGenerator.pyplot") as p:
            st.write(FakePyplot())

            p.assert_called_once()