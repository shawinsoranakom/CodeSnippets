def test_functools_wraps(self):
        """Test wrap for functools.wraps"""

        import streamlit as st

        @st.cache
        def f():
            return True

        self.assertEqual(True, hasattr(f, "__wrapped__"))