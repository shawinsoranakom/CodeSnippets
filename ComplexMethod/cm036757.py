def test_config_set_from_dict(self):
        """Test creating ConfigSet from dictionary data."""
        # Use realistic config data that helion.Config can handle
        config_data = {
            "block_sizes": [32, 16],
            "num_warps": 4,
            "num_stages": 3,
            "pid_type": "persistent_interleaved",
        }
        data = {"h100": {"batch_32_hidden_4096": config_data}}

        config_set = ConfigSet.from_dict("test_kernel", data)

        assert config_set.kernel_name == "test_kernel"
        assert config_set.get_platforms() == ["h100"]

        # Verify the config was created correctly
        config = config_set.get_config("h100", "batch_32_hidden_4096")
        assert isinstance(config, helion.Config)
        assert config.block_sizes == [32, 16]
        assert config.num_warps == 4
        assert config.num_stages == 3
        assert config.pid_type == "persistent_interleaved"