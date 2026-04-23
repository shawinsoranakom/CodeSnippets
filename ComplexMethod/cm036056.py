def test_getattr_with_cache(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VLLM_HOST_IP", "1.1.1.1")
    monkeypatch.setenv("VLLM_PORT", "1234")
    # __getattr__ is not decorated with functools.cache
    assert not hasattr(envs.__getattr__, "cache_info")

    # Enable envs cache and ignore ongoing environment changes
    enable_envs_cache()

    # __getattr__ is decorated with functools.cache
    assert hasattr(envs.__getattr__, "cache_info")
    start_hits = envs.__getattr__.cache_info().hits

    # 2 more hits due to VLLM_HOST_IP and VLLM_PORT accesses
    assert envs.VLLM_HOST_IP == "1.1.1.1"
    assert envs.VLLM_PORT == 1234
    assert envs.__getattr__.cache_info().hits == start_hits + 2

    # All environment variables are cached
    for environment_variable in environment_variables:
        envs.__getattr__(environment_variable)
    assert envs.__getattr__.cache_info().hits == start_hits + 2 + len(
        environment_variables
    )

    # Reset envs.__getattr__ back to none-cached version to
    # avoid affecting other tests
    envs.__getattr__ = envs.__getattr__.__wrapped__