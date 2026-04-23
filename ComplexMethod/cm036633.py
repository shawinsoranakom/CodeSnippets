def test_irecv_tensor_dict_send_allgather_postprocess_binds_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_irecv(t: torch.Tensor, *args: Any, **kwargs: Any) -> _DummyWork:
        t.fill_(1)
        return _DummyWork()

    monkeypatch.setattr(torch.distributed, "is_initialized", lambda: True)
    monkeypatch.setattr(torch.distributed, "irecv", fake_irecv)

    g = _make_group_for_unit_test(rank_in_group=0, world_size=2)
    # 2 tensors so we can catch late-binding bugs in postprocess closures.
    metadata_list = [
        ("a", TensorMetadata("cpu", torch.int32, torch.Size([4]))),
        ("b", TensorMetadata("cpu", torch.int32, torch.Size([4]))),
    ]
    g.recv_object = lambda src=None: metadata_list  # type: ignore[method-assign]

    ag = _DummyAllGatherGroup(world_size=2, rank_in_group=0)
    td, handles, postprocess = g.irecv_tensor_dict(all_gather_group=ag)

    assert td is not None
    assert len(handles) == 2
    assert len(postprocess) == 2

    # before postprocess, dict holds the TP slice (shape 2).
    assert td["a"].shape == torch.Size([2])
    assert td["b"].shape == torch.Size([2])

    # simulate worker-side "defer wait": wait + postprocess later.
    for handle in handles:
        handle.wait()
    for fn in postprocess:
        fn()

    # after postprocess, dict values are reconstructed to full shape (shape 4),
    # and each key should be updated independently
    assert td["a"].shape == torch.Size([4])
    assert td["b"].shape == torch.Size([4])
    torch.testing.assert_close(td["a"], torch.ones(4, dtype=torch.int32))
    torch.testing.assert_close(td["b"], torch.ones(4, dtype=torch.int32))