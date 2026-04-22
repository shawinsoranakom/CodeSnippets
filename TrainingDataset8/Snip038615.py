def test_max_message_size_default_values(self):
        self.assertEqual(200, config.get_option("server.maxMessageSize"))