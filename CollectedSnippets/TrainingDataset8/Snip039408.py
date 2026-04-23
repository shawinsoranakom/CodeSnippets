def test_cached_format_migration(self, _):
        @st.experimental_memo(persist="disk")
        def foo(i):
            st.text(i)
            return i

        # Executes normally, without raising any errors
        foo(1)