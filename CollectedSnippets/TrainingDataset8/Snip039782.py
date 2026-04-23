async def test_valid_script(self):
        script = """
import streamlit as st
st.write('test')
"""

        await self._check_script_loading(script, True, "ok")