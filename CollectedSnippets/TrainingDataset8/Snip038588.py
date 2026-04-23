def test_check_conflicts_server_port(self):
        config._set_option("global.developmentMode", True, "test")
        config._set_option("server.port", 1234, "test")
        with pytest.raises(AssertionError) as e:
            config._check_conflicts()
        self.assertEqual(
            str(e.value),
            "server.port does not work when global.developmentMode is true.",
        )