def test_get(self):
        test_configuration = {
            "TEST_ENABLED1": "1",
            "TEST_ENABLED2": True,
            "TEST_ENABLED3": 1,
            "TEST_ENABLED4": "True",
            "TEST_ENABLED5": "true",
            "TEST_ENABLED_WRONG": "on",
            "TEST_DISABLED1": "0",
            "TEST_DISABLED2": False,
            "TEST_DISABLED3": 0,
            "TEST_DISABLED4": "False",
            "TEST_DISABLED5": "false",
            "TEST_DISABLED_WRONG": "off",
            "TEST_INT1": 123,
            "TEST_INT2": "123",
            "TEST_FLOAT1": 123.45,
            "TEST_FLOAT2": "123.45",
            "TEST_LIST1": ["one", "two"],
            "TEST_LIST2": "one,two",
            "TEST_LIST3": "",
            "TEST_STR": "value",
            "TEST_DICT1": {"key1": "val1", "ke2": 3},
            "TEST_DICT2": '{"key1": "val1", "ke2": 3}',
        }
        settings = self.settings
        settings.attributes = {
            key: SettingsAttribute(value, 0)
            for key, value in test_configuration.items()
        }

        assert settings.getbool("TEST_ENABLED1")
        assert settings.getbool("TEST_ENABLED2")
        assert settings.getbool("TEST_ENABLED3")
        assert settings.getbool("TEST_ENABLED4")
        assert settings.getbool("TEST_ENABLED5")
        assert not settings.getbool("TEST_ENABLEDx")
        assert settings.getbool("TEST_ENABLEDx", True)
        assert not settings.getbool("TEST_DISABLED1")
        assert not settings.getbool("TEST_DISABLED2")
        assert not settings.getbool("TEST_DISABLED3")
        assert not settings.getbool("TEST_DISABLED4")
        assert not settings.getbool("TEST_DISABLED5")
        assert settings.getint("TEST_INT1") == 123
        assert settings.getint("TEST_INT2") == 123
        assert settings.getint("TEST_INTx") == 0
        assert settings.getint("TEST_INTx", 45) == 45
        assert settings.getfloat("TEST_FLOAT1") == 123.45
        assert settings.getfloat("TEST_FLOAT2") == 123.45
        assert settings.getfloat("TEST_FLOATx") == 0.0
        assert settings.getfloat("TEST_FLOATx", 55.0) == 55.0
        assert settings.getlist("TEST_LIST1") == ["one", "two"]
        assert settings.getlist("TEST_LIST2") == ["one", "two"]
        assert settings.getlist("TEST_LIST3") == []
        assert settings.getlist("TEST_LISTx") == []
        assert settings.getlist("TEST_LISTx", ["default"]) == ["default"]
        assert settings["TEST_STR"] == "value"
        assert settings.get("TEST_STR") == "value"
        assert settings["TEST_STRx"] is None
        assert settings.get("TEST_STRx") is None
        assert settings.get("TEST_STRx", "default") == "default"
        assert settings.getdict("TEST_DICT1") == {"key1": "val1", "ke2": 3}
        assert settings.getdict("TEST_DICT2") == {"key1": "val1", "ke2": 3}
        assert settings.getdict("TEST_DICT3") == {}
        assert settings.getdict("TEST_DICT3", {"key1": 5}) == {"key1": 5}
        with pytest.raises(
            ValueError,
            match=r"dictionary update sequence element #0 has length 3; 2 is required|sequence of pairs expected",
        ):
            settings.getdict("TEST_LIST1")
        with pytest.raises(
            ValueError, match="Supported values for boolean settings are"
        ):
            settings.getbool("TEST_ENABLED_WRONG")
        with pytest.raises(
            ValueError, match="Supported values for boolean settings are"
        ):
            settings.getbool("TEST_DISABLED_WRONG")