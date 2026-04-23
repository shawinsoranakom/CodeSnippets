def _parallel_worker(
    pgi: ProcessGroupInfo,
    vllm_config: VllmConfig,
    cpu_group,
    test_configs: list[MoETestConfig],
    verbosity: int,
    **kwargs,
) -> None:
    set_random_seed(7)

    total = 0
    passed = 0
    failed = 0
    fail_ids = []

    dp_rank = vllm_config.parallel_config.data_parallel_rank

    if current_platform.is_fp8_fnuz():
        override_normalize_e4m3fn_to_e4m3fnuz()

    for test_config in test_configs:
        cc = vllm_config.compilation_config
        if "from_forward_context" in cc.static_forward_context:
            del cc.static_forward_context["from_forward_context"]
            cc.static_all_moe_layers.remove("from_forward_context")

        tp_rank = pgi.rank % test_config.tp_size

        if verbosity > 0:
            print(f"subtest: {test_config.id()}", end="")

        try:
            _run_one_config(
                vllm_config,
                test_config.ep_size,
                test_config.dp_size,
                test_config.tp_size,
                dp_rank,
                tp_rank,
                test_config.m,
                test_config.n,
                test_config.k,
                test_config.num_experts,
                test_config.top_k,
                test_config.quantization,
                test_config.backend,
                functools.partial(
                    _test_body_config, test_config=test_config, cpu_group=cpu_group
                ),
                use_shared_experts=test_config.use_shared_experts,
                use_gate=test_config.use_gate,
                use_routed_input_transform=test_config.use_routed_input_transform,
            )
            if verbosity > 0:
                print(" PASSED")
            else:
                print(".", end="")
            passed = passed + 1
        except Exception as ex:
            fail_ids.append(test_config.id())
            failed = failed + 1
            if verbosity > 0:
                traceback.print_exc()
                print(f"\n{str(ex)}\nFAILED")
            else:
                print("F", end="")
        finally:
            # DeepEP managers are not reliably reusable across many subtests in
            # a single worker process. Tear them down after each DeepEP case so
            # later subtests do not inherit stale communication state.
            if test_config.backend in {
                "deepep_low_latency",
                "deepep_high_throughput",
            }:
                torch.accelerator.synchronize()
                all2all_manager = get_ep_group().device_communicator.all2all_manager
                if all2all_manager is not None:
                    all2all_manager.destroy()
            total = total + 1

    skipped = total - (passed + failed)

    fails = f"{failed} failed" if failed > 0 else ""
    sep = ", " if fails != "" else ""
    skips = f"{sep}{skipped} skipped" if skipped > 0 else ""
    sep = ", " if skips != "" or fails != "" else ""
    passes = f"{sep}{passed} passed" if passed > 0 else ""

    report = (
        f"============= {fails}{skips}{passes} of {total} total tests ============="
    )

    sep = "\n" if verbosity == 0 else ""
    print(f"{sep}{report}")

    if failed > 0:
        fail_ids_str = "\n".join(fail_ids)
        raise RuntimeError(
            f"\n============= Failed subtests =============\n{fail_ids_str}\n{report}"
        )