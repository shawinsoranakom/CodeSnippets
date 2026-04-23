def test_pipeline_defaults(self, host):
    # TODO: parameterize the defaults so we don't rely on hard-coded values in xx

    assert URLFile.pool_manager().pools._maxsize == 10# PoolManager num_pools param
    pool_manager_defaults = {
      "maxsize": 100,
      "socket_options": [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),],
    }
    for k, v in pool_manager_defaults.items():
      assert URLFile.pool_manager().connection_pool_kw.get(k) == v

    retry_defaults = {
      "total": 5,
      "backoff_factor": 0.5,
      "status_forcelist": [409, 429, 503, 504],
    }
    for k, v in retry_defaults.items():
      assert getattr(URLFile.pool_manager().connection_pool_kw["retries"], k) == v

    # ensure caching on by default and cache dir gets created
    os.environ.pop("DISABLE_FILEREADER_CACHE", None)
    if os.path.exists(Paths.download_cache_root()):
      shutil.rmtree(Paths.download_cache_root())
    URLFile(f"{host}/test.txt").get_length()
    URLFile(f"{host}/test.txt").read()
    assert os.path.exists(Paths.download_cache_root())