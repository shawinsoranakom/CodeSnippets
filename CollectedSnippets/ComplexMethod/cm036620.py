def test_env_var_and_runtime_env_propagation():
    """
    Verify env vars (NCCL_, HF_) and parallel_config.ray_runtime_env
    propagate to RayWorkerProc actors.
    """
    sentinel_vars = {
        "NCCL_DEBUG": "INFO",
        "HF_TOKEN": "test_sentinel_token",
    }
    for k, v in sentinel_vars.items():
        os.environ[k] = v

    try:
        # Called directly (not via the ray_init fixture) because sentinel
        # env vars must be in os.environ before ray.init() so that Ray
        # worker processes inherit them.
        _ray_init()

        pg = ray.util.placement_group([{"GPU": 1, "CPU": 1}] * 2, strategy="PACK")
        ray.get(pg.ready())

        # Include the project root so that RayWorkerProc actors can
        # unpickle _get_env_var.
        project_root = str(pathlib.Path(__file__).resolve().parents[2])
        ray_runtime_env = {
            "env_vars": {
                "RAY_RUNTIME_ENV_TEST": "ray_runtime_env",
                "PYTHONPATH": project_root,
            },
        }

        actor = AsyncLLMActor.remote()
        ray.get(actor.start.remote(pg, ray_runtime_env=ray_runtime_env))

        all_env_names = list(sentinel_vars) + ["RAY_RUNTIME_ENV_TEST"]
        text, env_results = ray.get(
            actor.generate_and_get_worker_envs.remote("Hello world", all_env_names)
        )
        assert len(text) > 0

        for name, expected in sentinel_vars.items():
            for val in env_results[name]:
                assert val == expected

        for val in env_results["RAY_RUNTIME_ENV_TEST"]:
            assert val == "ray_runtime_env"

    finally:
        for k in sentinel_vars:
            os.environ.pop(k, None)