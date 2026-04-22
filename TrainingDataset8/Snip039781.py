async def test_invalid_script(self):
        script = """
import streamlit as st
st.not_a_function('test')
"""

        await self._check_script_loading(script, False, "error")