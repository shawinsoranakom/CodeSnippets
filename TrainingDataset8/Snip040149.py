def test_open_browser(self, os_type, webbrowser_expect, popen_expect):
        """Test web browser opening scenarios."""
        from streamlit import env_util

        env_util.IS_WINDOWS = os_type == "Windows"
        env_util.IS_DARWIN = os_type == "Darwin"
        env_util.IS_LINUX_OR_BSD = os_type == "Linux"

        with patch("streamlit.env_util.is_executable_in_path", return_value=True):
            with patch("webbrowser.open") as webbrowser_open:
                with patch("subprocess.Popen") as subprocess_popen:
                    util.open_browser("http://some-url")
                    self.assertEqual(webbrowser_expect, webbrowser_open.called)
                    self.assertEqual(popen_expect, subprocess_popen.called)