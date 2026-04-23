def test_warning_memo_ttl_persist(self, _):
        """Using @st.experimental_memo with ttl and persist produces a warning."""
        with self.assertLogs(
            "streamlit.runtime.caching.memo_decorator", level=logging.WARNING
        ) as logs:

            @st.experimental_memo(ttl=60, persist="disk")
            def user_function():
                return 42

            st.write(user_function())

            output = "".join(logs.output)
            self.assertIn(
                "The memoized function 'user_function' has a TTL that will be ignored.",
                output,
            )