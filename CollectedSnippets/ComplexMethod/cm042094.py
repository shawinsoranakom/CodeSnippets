async def test_ext_env():
    env = ForTestEnv()
    assert len(env_read_api_registry) > 0
    assert len(env_write_api_registry) > 0

    apis = env.get_all_available_apis(mode="read")
    assert len(apis) > 0
    assert len(apis["read_api"]) == 3

    _ = await env.write_thru_api(EnvAPIAbstract(api_name="write_api", kwargs={"a": 5, "b": 10}))
    assert env.value == 15

    with pytest.raises(KeyError):
        await env.read_from_api("not_exist_api")

    assert await env.read_from_api("read_api_no_param") == 15
    assert await env.read_from_api(EnvAPIAbstract(api_name="read_api", kwargs={"a": 5, "b": 5})) == 10