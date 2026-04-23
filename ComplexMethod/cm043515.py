def test_specific_values(self):
        config = BenchConfig(
            apps=AppsConfig(
                active=False,
                test_start_index=1,
                test_end_index=2,
                train_start_index=3,
                train_end_index=4,
            ),
            mbpp=MbppConfig(active=False, test_len=5, train_len=6),
            gptme=GptmeConfig(active=False),
        )
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