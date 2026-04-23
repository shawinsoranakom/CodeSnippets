def send_recv_tensor_dict_test_worker(
    monkeypatch: pytest.MonkeyPatch,
    tp_size: int,
    pp_size: int,
    rank: int,
    distributed_init_port: str,
):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    device = torch.device(f"cuda:{rank}")
    torch.accelerator.set_device_index(device)
    init_test_distributed_environment(tp_size, pp_size, rank, distributed_init_port)

    test_dict = {
        # device tensor
        "a": torch.arange(8, dtype=torch.float32, device="cuda"),
        # CPU tensor
        "b": torch.arange(16, dtype=torch.int8, device="cpu"),
        "c": "test",
        "d": [1, 2, 3],
        "e": {"a": 1, "b": 2},
        # empty tensor
        "f": torch.tensor([], dtype=torch.float32, device="cuda"),
    }

    if not get_pp_group().is_first_rank:
        recv_dict = get_pp_group().recv_tensor_dict()

    if not get_pp_group().is_last_rank:
        get_pp_group().send_tensor_dict(test_dict)

    if not get_pp_group().is_first_rank:
        assert len(recv_dict) == len(test_dict)
        torch.testing.assert_close(recv_dict["a"], test_dict["a"])
        torch.testing.assert_close(recv_dict["b"], test_dict["b"])
        assert recv_dict["c"] == test_dict["c"]
        assert recv_dict["d"] == test_dict["d"]
        assert recv_dict["e"] == test_dict["e"]
        torch.testing.assert_close(recv_dict["f"], test_dict["f"])