def _test_worker_info_init_fn(worker_id):
    worker_info = torch.utils.data.get_worker_info()
    if worker_id != worker_info.id:
        raise AssertionError("worker_init_fn and worker_info should have consistent id")
    if worker_id >= worker_info.num_workers:
        raise AssertionError("worker_init_fn and worker_info should have valid id")
    if worker_info.seed != torch.initial_seed():
        raise AssertionError(
            "worker_init_fn and worker_info should have consistent seed"
        )
    dataset = worker_info.dataset
    if not isinstance(dataset, TestWorkerInfoDataset):
        raise AssertionError("worker_info should have correct dataset copy")
    if hasattr(dataset, "value"):
        raise AssertionError("worker_info should have correct dataset copy")
    for k in ["id", "num_workers", "seed", "dataset", "rng"]:
        if f"{k}=" not in repr(worker_info):
            raise AssertionError(f"Expected {k} in worker_info repr")
    dataset.value = [worker_id, os.getpid()]