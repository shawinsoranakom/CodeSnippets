def test_get_platform_configs(self):
        """Test getting all configs for a specific platform."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_1 = {"num_warps": 4, "num_stages": 3, "block_sizes": [64, 32]}
            config_2 = {"num_warps": 8, "num_stages": 5, "block_sizes": [128, 64]}
            default_config = {
                "num_warps": 16,
                "num_stages": 7,
                "block_sizes": [256, 128],
            }
            config_3 = {"num_warps": 2, "num_stages": 2, "block_sizes": [32, 16]}

            kernel_dir = Path(temp_dir) / "test_kernel"
            kernel_dir.mkdir()
            with open(kernel_dir / "h100.json", "w") as f:
                json.dump(
                    {
                        "batch_32_hidden_4096": config_1,
                        "batch_64_hidden_2048": config_2,
                        "default": default_config,
                    },
                    f,
                )
            with open(kernel_dir / "a100.json", "w") as f:
                json.dump({"batch_16_hidden_1024": config_3}, f)

            manager = ConfigManager(base_dir=temp_dir)

            h100_configs = manager.get_platform_configs("test_kernel", "h100")
            assert len(h100_configs) == 3
            assert "batch_32_hidden_4096" in h100_configs
            assert "batch_64_hidden_2048" in h100_configs
            assert "default" in h100_configs
            for config in h100_configs.values():
                assert isinstance(config, helion.Config)

            assert h100_configs["batch_32_hidden_4096"].num_warps == 4
            assert h100_configs["default"].num_stages == 7

            a100_configs = manager.get_platform_configs("test_kernel", "a100")
            assert len(a100_configs) == 1
            assert "batch_16_hidden_1024" in a100_configs
            assert isinstance(a100_configs["batch_16_hidden_1024"], helion.Config)
            assert a100_configs["batch_16_hidden_1024"].num_warps == 2

            nonexistent_configs = manager.get_platform_configs("test_kernel", "v100")
            assert len(nonexistent_configs) == 0