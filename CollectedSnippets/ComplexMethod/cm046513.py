def test_cuda_path_returns_correct_fields(self):
        mock_props = MagicMock()
        mock_props.total_memory = 16 * (1024**3)
        mock_props.name = "NVIDIA Test GPU"

        with (
            patch("utils.hardware.hardware.get_device", return_value = DeviceType.CUDA),
            patch("torch.cuda.current_device", return_value = 0),
            patch("torch.cuda.get_device_properties", return_value = mock_props),
            patch("torch.cuda.memory_allocated", return_value = 4 * (1024**3)),
            patch("torch.cuda.memory_reserved", return_value = 6 * (1024**3)),
        ):
            result = get_gpu_memory_info()

        assert result["available"] is True
        assert result["backend"] == "cuda"
        assert result["device_name"] == "NVIDIA Test GPU"
        assert abs(result["total_gb"] - 16.0) < 0.01
        assert abs(result["allocated_gb"] - 4.0) < 0.01
        assert abs(result["free_gb"] - 12.0) < 0.01
        assert abs(result["utilization_pct"] - 25.0) < 0.1