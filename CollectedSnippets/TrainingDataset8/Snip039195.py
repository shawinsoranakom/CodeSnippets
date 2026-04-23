def test_return_true_when_submitted(self):
        with st.form("form"):
            submitted = st.form_submit_button("Submit")
            self.assertEqual(submitted, True)