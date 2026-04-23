def test_tracing_enable_disable(
    mock_get_client: MagicMock, *, enabled: bool | None, env: str
) -> None:
    mock_session = MagicMock()
    mock_client_ = Client(
        session=mock_session, api_key="test", auto_batch_tracing=False
    )
    mock_get_client.return_value = mock_client_

    def my_func(a: int) -> int:
        return a + 1

    if hasattr(get_env_var, "cache_clear"):
        get_env_var.cache_clear()  # type: ignore[attr-defined]
    env_on = env == "true"
    with (
        patch.dict("os.environ", {"LANGSMITH_TRACING": env}),
        tracing_context(enabled=enabled),
    ):
        RunnableLambda(my_func).invoke(1)

    mock_posts = _get_posts(mock_client_)
    if enabled is True:
        assert len(mock_posts) == 1
    elif enabled is False:
        assert not mock_posts
    elif env_on:
        assert len(mock_posts) == 1
    else:
        assert not mock_posts