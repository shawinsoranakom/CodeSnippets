def test_get_option(self):
        config._set_option("browser.serverAddress", "some.bucket", "test")
        self.assertEqual("some.bucket", config.get_option("browser.serverAddress"))

        with pytest.raises(RuntimeError) as e:
            config.get_option("doesnt.exist")
        self.assertEqual(str(e.value), 'Config key "doesnt.exist" not defined.')