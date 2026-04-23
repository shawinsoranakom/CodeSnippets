def test_no_exception_for_callbacks_on_submit_button(self):
        with st.form("form"):
            st.radio("radio", ["a", "b", "c"], 0)
            st.form_submit_button(on_click=lambda x: x)