def test_from_dict_valid_dict(self):
        config_dict = {
            "apps": {
                "active": False,
                "test_start_index": 1,
                "test_end_index": 2,
                "train_start_index": 3,
                "train_end_index": 4,
            },
            "mbpp": {"active": False, "test_len": 5, "train_len": 6},
            "gptme": {"active": False},
        }
        config = BenchConfig.from_dict(config_dict)
        assert isinstance(config.apps, AppsConfig)
        assert isinstance(config.mbpp, MbppConfig)
        assert isinstance(config.gptme, GptmeConfig)
        assert config.apps.active is False
        assert config.apps.test_start_index == 1
        assert config.apps.test_end_index == 2
        assert config.apps.train_start_index == 3
        assert config.apps.train_end_index == 4
        assert config.mbpp.active is False
        assert config.mbpp.test_len == 5
        assert config.mbpp.train_len == 6
        assert config.gptme.active is False