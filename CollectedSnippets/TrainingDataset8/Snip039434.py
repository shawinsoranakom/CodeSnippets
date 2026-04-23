def setUp(self):
        # Guard against external tests not properly cache-clearing
        # in their teardowns.
        st.experimental_singleton.clear()