def test_parse_update_info_pickled(self, monkeypatch):
        """Test parsing update info with pickled IPC handles (HTTP path)."""
        if torch.accelerator.device_count() < 1:
            pytest.skip("Need at least 1 GPU for this test")

        monkeypatch.setenv("VLLM_ALLOW_INSECURE_SERIALIZATION", "1")

        config = WeightTransferConfig(backend="ipc")
        parallel_config = create_mock_parallel_config()
        engine = IPCWeightTransferEngine(config, parallel_config)

        dummy_tensor1 = torch.ones(100, 100, device="cuda:0")
        dummy_tensor2 = torch.ones(50, device="cuda:0")
        ipc_handle1 = reduce_tensor(dummy_tensor1)
        ipc_handle2 = reduce_tensor(dummy_tensor2)
        gpu_uuid = str(torch.cuda.get_device_properties(0).uuid)
        ipc_handles = [{gpu_uuid: ipc_handle1}, {gpu_uuid: ipc_handle2}]

        pickled = base64.b64encode(pickle.dumps(ipc_handles)).decode("utf-8")

        update_info = engine.parse_update_info(
            {
                "names": ["w1", "w2"],
                "dtype_names": ["float32", "bfloat16"],
                "shapes": [[100, 100], [50]],
                "ipc_handles_pickled": pickled,
            }
        )

        assert isinstance(update_info, IPCWeightTransferUpdateInfo)
        assert update_info.names == ["w1", "w2"]
        assert len(update_info.ipc_handles) == 2
        assert update_info.ipc_handles_pickled is None
        assert gpu_uuid in update_info.ipc_handles[0]
        assert gpu_uuid in update_info.ipc_handles[1]