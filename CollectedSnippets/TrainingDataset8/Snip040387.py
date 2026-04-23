def test_spinner(self):
        """Test st.spinner."""
        # TODO(armando): Test that the message is actually passed to
        # message.warning
        with patch("streamlit.delta_generator.DeltaGenerator.empty") as e:
            with st.spinner("some message"):
                time.sleep(0.15)
            e.assert_called_once_with()