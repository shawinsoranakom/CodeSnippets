def test_server_headless(self):
        orig_display = None
        if "DISPLAY" in os.environ.keys():
            orig_display = os.environ["DISPLAY"]
            del os.environ["DISPLAY"]

        orig_is_linux_or_bsd = env_util.IS_LINUX_OR_BSD
        env_util.IS_LINUX_OR_BSD = True

        self.assertEqual(True, config.get_option("server.headless"))

        env_util.IS_LINUX_OR_BSD = orig_is_linux_or_bsd
        if orig_display:
            os.environ["DISPLAY"] = orig_display