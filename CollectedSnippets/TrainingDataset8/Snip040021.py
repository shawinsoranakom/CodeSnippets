def test_disabled_parameter_id_download_button(self):
        st.download_button("my_widget", data="")

        with self.assertRaises(errors.DuplicateWidgetID):
            st.download_button("my_widget", data="", disabled=True)