def test_run_warning_absence(self):
        """Using Streamlit through the CLI results in a Runtime being instantiated,
        so it produces no usage warning."""
        with self.assertLogs(level=logging.WARNING) as logs:
            delta_generator._use_warning_has_been_displayed = False
            st.write("Using delta generator")
            # assertLogs is being used as a context manager, but it also checks
            # that some log output was captured, so we have to let it capture something
            get_logger("root").warning("irrelevant warning so assertLogs passes")
            self.assertNotRegex("".join(logs.output), r"streamlit run")