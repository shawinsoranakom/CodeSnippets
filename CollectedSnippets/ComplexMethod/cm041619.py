def _is_close(batch_a: dict[str, Any], batch_b: dict[str, Any]) -> None:
    assert batch_a.keys() == batch_b.keys()
    for key in batch_a.keys():
        if isinstance(batch_a[key], torch.Tensor):
            assert torch.allclose(batch_a[key], batch_b[key], rtol=1e-4, atol=1e-5)
        elif isinstance(batch_a[key], list) and all(isinstance(item, torch.Tensor) for item in batch_a[key]):
            assert len(batch_a[key]) == len(batch_b[key])
            for tensor_a, tensor_b in zip(batch_a[key], batch_b[key]):
                assert torch.allclose(tensor_a, tensor_b, rtol=1e-4, atol=1e-5)
        else:
            assert batch_a[key] == batch_b[key]