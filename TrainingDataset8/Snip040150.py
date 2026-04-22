def test_open_browser_linux_no_xdg(self):
        """Test opening the browser on Linux with no xdg installed"""
        from streamlit import env_util

        env_util.IS_LINUX_OR_BSD = True

        with patch("streamlit.env_util.is_executable_in_path", return_value=False):
            with patch("webbrowser.open") as webbrowser_open:
                with patch("subprocess.Popen") as subprocess_popen:
                    util.open_browser("http://some-url")
                    self.assertEqual(True, webbrowser_open.called)
                    self.assertEqual(False, subprocess_popen.called)