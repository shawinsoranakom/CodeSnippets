def test_default_values(self):
        config = BenchConfig()
        assert isinstance(config.apps, AppsConfig)
        assert isinstance(config.mbpp, MbppConfig)
        assert isinstance(config.gptme, GptmeConfig)
        assert config.apps.active is True
        assert config.apps.test_start_index == 0
        assert config.apps.test_end_index == 1
        assert config.apps.train_start_index == 0
        assert config.apps.train_end_index == 0
        assert config.mbpp.active is True
        assert config.mbpp.test_len == 1
        assert config.mbpp.train_len == 0
        assert config.gptme.active is True