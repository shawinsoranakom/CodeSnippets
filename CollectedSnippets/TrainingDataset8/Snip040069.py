def test_stop(self):
        with pytest.raises(StopException) as exc_message:
            st.stop()