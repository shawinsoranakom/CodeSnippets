def test_return_false_when_not_submitted(self):
        with st.form("form1"):
            submitted = st.form_submit_button("Submit")
            self.assertEqual(submitted, False)