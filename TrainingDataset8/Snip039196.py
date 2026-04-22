def test_exception_for_callbacks_on_widgets(self):
        with self.assertRaises(StreamlitAPIException):
            with st.form("form"):
                st.radio("radio", ["a", "b", "c"], 0, on_change=lambda x: x)
                st.form_submit_button()