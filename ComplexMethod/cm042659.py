def test_update(self):
        settings = BaseSettings({"key_lowprio": 0}, priority=0)
        settings.set("key_highprio", 10, priority=50)
        custom_settings = BaseSettings(
            {"key_lowprio": 1, "key_highprio": 11}, priority=30
        )
        custom_settings.set("newkey_one", None, priority=50)
        custom_dict = {"key_lowprio": 2, "key_highprio": 12, "newkey_two": None}

        settings.update(custom_dict, priority=20)
        assert settings["key_lowprio"] == 2
        assert settings.getpriority("key_lowprio") == 20
        assert settings["key_highprio"] == 10
        assert "newkey_two" in settings
        assert settings.getpriority("newkey_two") == 20

        settings.update(custom_settings)
        assert settings["key_lowprio"] == 1
        assert settings.getpriority("key_lowprio") == 30
        assert settings["key_highprio"] == 10
        assert "newkey_one" in settings
        assert settings.getpriority("newkey_one") == 50

        settings.update({"key_lowprio": 3}, priority=20)
        assert settings["key_lowprio"] == 1