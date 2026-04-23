def test_browser_server_port(self):
        # developmentMode must be False for server.port to be modified
        config.set_option("global.developmentMode", False)
        config.set_option("server.port", 1234)
        self.assertEqual(1234, config.get_option("browser.serverPort"))