def test_run_warning_presence(self):
        """Using Streamlit without `streamlit run` produces a warning."""
        with self.assertLogs(level=logging.WARNING) as logs:
            delta_generator._use_warning_has_been_displayed = False
            st.write("Using delta generator")
            output = "".join(logs.output)
            # Warning produced exactly once
            self.assertEqual(len(re.findall(r"streamlit run", output)), 1)