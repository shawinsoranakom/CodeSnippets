def test_async_intermediate_tensors_lazy_wait() -> None:
    work = _DummyWork()
    post_calls = {"n": 0}

    def post() -> None:
        post_calls["n"] += 1

    it = AsyncIntermediateTensors(
        {"x": torch.tensor([1])},
        comm_handles=[work],
        comm_postprocess=[post],
    )

    # accessing non-tensor attributes should not trigger wait.
    assert it.kv_connector_output is None
    assert work.wait_calls == 0
    assert post_calls["n"] == 0

    # first access of `.tensors` triggers wait + postprocess.
    _ = it.tensors
    assert work.wait_calls == 1
    assert post_calls["n"] == 1

    # subsequent access should not re-wait.
    _ = it.tensors
    assert work.wait_calls == 1
    assert post_calls["n"] == 1