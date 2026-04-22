async def test_timeout_script(self):
        script = """
import time
time.sleep(5)
"""

        with patch("streamlit.runtime.runtime.SCRIPT_RUN_CHECK_TIMEOUT", new=0.1):
            await self._check_script_loading(script, False, "timeout")