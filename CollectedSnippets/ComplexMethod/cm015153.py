def _test_get_worker_info():
    # get_worker_info returns None in main proc
    if torch.utils.data.get_worker_info() is not None:
        raise AssertionError("Expected get_worker_info() to return None in main proc")
    num_workers = 2
    batch_size = 2
    dataset = TestWorkerInfoDataset(6, batch_size, num_workers)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        worker_init_fn=_test_worker_info_init_fn,
    )
    it = iter(dataloader)
    data = []
    for d in it:
        data.append(d)  # noqa: PERF402
    worker_pids = [w.pid for w in it._workers]
    data = torch.cat(data, 0)
    for d in data:
        # each `d` is a [worker_id, worker_pid] pair, which is set in
        # _test_worker_info_init_fn
        if d[1] != worker_pids[d[0]]:
            raise AssertionError(f"Expected worker pid {worker_pids[d[0]]}, got {d[1]}")
    # get_worker_info returns None in main proc after data loading
    if torch.utils.data.get_worker_info() is not None:
        raise AssertionError(
            "Expected get_worker_info() to return None after data loading"
        )
    # main proc dataset was never assigned this attribute
    if hasattr(dataset, "value"):
        raise AssertionError("Expected main dataset to not have 'value' attribute")
    try:
        _ = dataset[0]
    except AttributeError:
        return
    raise RuntimeError("Expected AttributeError")