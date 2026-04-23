def gpu_p2p_access_check(src: int, tgt: int) -> bool:
    """Check if GPU src can access GPU tgt."""

    # if the cache variable is already calculated,
    # read from the cache instead of checking it again
    global _gpu_p2p_access_cache
    if _gpu_p2p_access_cache is not None:
        return _gpu_p2p_access_cache[f"{src}->{tgt}"]

    is_distributed = dist.is_initialized()

    num_dev = current_platform.device_count()
    cuda_visible_devices = envs.CUDA_VISIBLE_DEVICES
    if cuda_visible_devices is None:
        cuda_visible_devices = ",".join(str(i) for i in range(num_dev))

    path = os.path.join(
        envs.VLLM_CACHE_ROOT, f"gpu_p2p_access_cache_for_{cuda_visible_devices}.json"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    from vllm.distributed.parallel_state import get_world_group

    if (not is_distributed or get_world_group().local_rank == 0) and (
        not os.path.exists(path)
    ):
        # only the local master process (with local_rank == 0) can
        #  enter this block to calculate the cache
        logger.info("generating GPU P2P access cache in %s", path)
        cache: dict[str, bool] = {}
        ids = list(range(num_dev))
        # batch of all pairs of GPUs
        batch_src, batch_tgt = zip(*list(product(ids, ids)))
        # NOTE: we use `subprocess` rather than `multiprocessing` here
        # because the caller might not have `if __name__ == "__main__":`,
        # in that case we cannot use spawn method in multiprocessing.
        # However, `can_actually_p2p` requires spawn method.
        # The fix is, we use `subprocess` to call the function,
        # where we have `if __name__ == "__main__":` in this file.

        # use a temporary file to store the result
        # we don't use the output of the subprocess directly,
        # because the subprocess might produce logging output
        with tempfile.NamedTemporaryFile() as output_file:
            input_bytes = pickle.dumps((batch_src, batch_tgt, output_file.name))
            returned = subprocess.run(
                [sys.executable, __file__], input=input_bytes, capture_output=True
            )
            # check if the subprocess is successful
            try:
                returned.check_returncode()
            except Exception as e:
                # wrap raised exception to provide more information
                raise RuntimeError(
                    f"Error happened when batch testing "
                    f"peer-to-peer access from {batch_src} to {batch_tgt}:\n"
                    f"{returned.stderr.decode()}"
                ) from e
            with open(output_file.name, "rb") as f:
                result = pickle.load(f)
        for _i, _j, r in zip(batch_src, batch_tgt, result):
            cache[f"{_i}->{_j}"] = r
        with open(path, "w") as f:
            json.dump(cache, f, indent=4)
    if is_distributed:
        get_world_group().barrier()
    logger.info("reading GPU P2P access cache from %s", path)
    with open(path) as f:
        cache = json.load(f)
    _gpu_p2p_access_cache = cache
    return _gpu_p2p_access_cache[f"{src}->{tgt}"]