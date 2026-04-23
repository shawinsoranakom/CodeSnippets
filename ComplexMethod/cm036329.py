async def test_engine_core_client_util_method_nested_structures(
    monkeypatch: pytest.MonkeyPatch,
    subprocess_echo_dc_nested_patch,
):
    with monkeypatch.context() as m:
        # Must set insecure serialization to allow returning custom types.
        m.setenv("VLLM_ALLOW_INSECURE_SERIALIZATION", "1")

        # Monkey-patch core engine utility function to test.
        m.setattr(EngineCore, "echo_dc_nested", echo_dc_nested, raising=False)

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
            core_client: AsyncMPClient = client

            # Test list of dicts: [{"a": val, "b": val}, {"c": val, "d": val}]
            result = await core_client.call_utility_async(
                "echo_dc_nested", "nested1", "list_of_dicts"
            )
            assert isinstance(result, list) and len(result) == 2
            for i, item in enumerate(result):
                assert isinstance(item, dict)
                if i == 0:
                    assert "a" in item and "b" in item
                    assert (
                        isinstance(item["a"], TestMessage)
                        and item["a"].message == "nested1"
                    )
                    assert (
                        isinstance(item["b"], TestMessage)
                        and item["b"].message == "nested1"
                    )
                else:
                    assert "c" in item and "d" in item
                    assert (
                        isinstance(item["c"], TestMessage)
                        and item["c"].message == "nested1"
                    )
                    assert (
                        isinstance(item["d"], TestMessage)
                        and item["d"].message == "nested1"
                    )

            # Test dict of lists: {"list1": [val, val], "list2": [val, val]}
            result = await core_client.call_utility_async(
                "echo_dc_nested", "nested2", "dict_of_lists"
            )
            assert isinstance(result, dict) and len(result) == 2
            assert "list1" in result and "list2" in result
            for key, lst in result.items():
                assert isinstance(lst, list) and len(lst) == 2
                for item in lst:
                    assert isinstance(item, TestMessage) and item.message == "nested2"

            # Test deeply nested: {"outer": [{"inner": [val, val]},
            # {"inner": [val]}]}
            result = await core_client.call_utility_async(
                "echo_dc_nested", "nested3", "deep_nested"
            )
            assert isinstance(result, dict) and "outer" in result
            outer_list = result["outer"]
            assert isinstance(outer_list, list) and len(outer_list) == 2

            # First dict in outer list should have "inner" with 2 items
            inner_dict1 = outer_list[0]
            assert isinstance(inner_dict1, dict) and "inner" in inner_dict1
            inner_list1 = inner_dict1["inner"]
            assert isinstance(inner_list1, list) and len(inner_list1) == 2
            for item in inner_list1:
                assert isinstance(item, TestMessage) and item.message == "nested3"

            # Second dict in outer list should have "inner" with 1 item
            inner_dict2 = outer_list[1]
            assert isinstance(inner_dict2, dict) and "inner" in inner_dict2
            inner_list2 = inner_dict2["inner"]
            assert isinstance(inner_list2, list) and len(inner_list2) == 1
            assert (
                isinstance(inner_list2[0], TestMessage)
                and inner_list2[0].message == "nested3"
            )

            # Test with None values in nested structures
            result = await core_client.call_utility_async(
                "echo_dc_nested", None, "list_of_dicts"
            )
            assert isinstance(result, list) and len(result) == 2
            for item in result:
                assert isinstance(item, dict)
                for val in item.values():
                    assert val is None

        finally:
            client.shutdown()