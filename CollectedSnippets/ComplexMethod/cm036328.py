async def test_engine_core_client_util_method_custom_dict_return(
    monkeypatch: pytest.MonkeyPatch,
    subprocess_echo_dc_dict_patch,
):
    with monkeypatch.context() as m:
        # Must set insecure serialization to allow returning custom types.
        m.setenv("VLLM_ALLOW_INSECURE_SERIALIZATION", "1")

        # Monkey-patch core engine utility function to test.
        m.setattr(EngineCore, "echo_dc_dict", echo_dc_dict, raising=False)

        engine_args = EngineArgs(model=MODEL_NAME, enforce_eager=True)
        vllm_config = engine_args.create_engine_config(
            usage_context=UsageContext.UNKNOWN_CONTEXT
        )
        executor_class = Executor.get_class(vllm_config)

        with set_default_torch_num_threads(1):
            client = EngineCoreClient.make_client(
                multiprocess_mode=True,
                asyncio_mode=True,
                vllm_config=vllm_config,
                executor_class=executor_class,
                log_stats=True,
            )

        try:
            # Test utility method returning custom / non-native data type.
            core_client: AsyncMPClient = client

            # Test single object return
            result = await core_client.call_utility_async(
                "echo_dc_dict", "testarg3", False
            )
            assert isinstance(result, TestMessage) and result.message == "testarg3"

            # Test dict return with custom value types
            result = await core_client.call_utility_async(
                "echo_dc_dict", "testarg3", True
            )
            assert isinstance(result, dict) and len(result) == 3
            for key, val in result.items():
                assert key in ["key1", "key2", "key3"]
                assert isinstance(val, TestMessage) and val.message == "testarg3"

            # Test returning dict with None values
            result = await core_client.call_utility_async("echo_dc_dict", None, True)
            assert isinstance(result, dict) and len(result) == 3
            for key, val in result.items():
                assert key in ["key1", "key2", "key3"]
                assert val is None

        finally:
            client.shutdown()