def test_amd_smi_json_parsing(self):
        """Verify _extract_gpu_metrics parses amd-smi JSON correctly."""
        amd_path = PACKAGE_ROOT / "studio" / "backend" / "utils" / "hardware" / "amd.py"
        _amd_spec = importlib.util.spec_from_file_location("test_amd", amd_path)
        assert _amd_spec is not None and _amd_spec.loader is not None
        amd_mod = importlib.util.module_from_spec(_amd_spec)

        sys.modules["loggers"] = MagicMock()
        sys.modules["loggers"].get_logger = MagicMock(return_value = MagicMock())

        try:
            _amd_spec.loader.exec_module(amd_mod)
        except Exception:
            pytest.skip("Could not load amd module in test environment")

        # Simulate amd-smi metric JSON output
        gpu_data = {
            "usage": {"gfx_activity": "85"},
            "temperature": {"edge": "72"},
            "power": {
                "current_socket_power": "200.5",
                "power_cap": "300",
            },
            "vram": {
                "vram_used": 8192,  # MB
                "vram_total": 16384,  # MB
            },
        }
        metrics = amd_mod._extract_gpu_metrics(gpu_data)
        assert metrics["gpu_utilization_pct"] == 85.0
        assert metrics["temperature_c"] == 72.0
        assert metrics["power_draw_w"] == 200.5
        assert metrics["power_limit_w"] == 300.0
        assert metrics["vram_used_gb"] == round(8192 / 1024, 2)
        assert metrics["vram_total_gb"] == round(16384 / 1024, 2)
        assert metrics["vram_utilization_pct"] is not None
        assert metrics["power_utilization_pct"] is not None