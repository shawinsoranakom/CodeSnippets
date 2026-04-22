def test_update_config_with_toml(self):
        self.assertEqual(True, config.get_option("client.caching"))
        toml = textwrap.dedent(
            """
           [client]
           caching = false
        """
        )
        config._update_config_with_toml(toml, "test")
        self.assertEqual(False, config.get_option("client.caching"))