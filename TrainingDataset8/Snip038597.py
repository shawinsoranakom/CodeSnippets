def test_get_where_defined(self):
        config._set_option("browser.serverAddress", "some.bucket", "test")
        self.assertEqual("test", config.get_where_defined("browser.serverAddress"))

        with pytest.raises(RuntimeError) as e:
            config.get_where_defined("doesnt.exist")
        self.assertEqual(str(e.value), 'Config key "doesnt.exist" not defined.')