def test_http_socket_options_none_vs_empty_tuple_vs_populated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discriminates the three input shapes at the builder boundary.

    Also locks the no-filter contract for user overrides: the populated-case
    assertion is verbatim, proving `_resolve_socket_options` does not run
    user overrides through `_filter_supported`.
    """
    recorded: list[tuple[str, tuple, tuple]] = []

    def spy_async(
        base_url: str | None,
        timeout: Any,
        socket_options: tuple = (),
    ) -> Any:
        recorded.append(("async", (base_url, timeout), tuple(socket_options)))
        # Return a real (but unused) client so init completes.
        return _client_utils._AsyncHttpxClientWrapper(
            base_url=base_url or "https://api.openai.com/v1", timeout=timeout
        )

    def spy_sync(
        base_url: str | None,
        timeout: Any,
        socket_options: tuple = (),
    ) -> Any:
        recorded.append(("sync", (base_url, timeout), tuple(socket_options)))
        return _client_utils._SyncHttpxClientWrapper(
            base_url=base_url or "https://api.openai.com/v1", timeout=timeout
        )

    monkeypatch.setattr(
        "langchain_openai.chat_models.base._get_default_async_httpx_client",
        spy_async,
    )
    monkeypatch.setattr(
        "langchain_openai.chat_models.base._get_default_httpx_client",
        spy_sync,
    )

    # (1) Unset -> None -> env-driven defaults (non-empty on linux/darwin CI).
    ChatOpenAI(model="gpt-4o")
    assert recorded, "expected a default-client build"
    _, _, opts1 = recorded[-1]
    assert isinstance(opts1, tuple)

    # (2) Explicit empty tuple -> ().
    recorded.clear()
    ChatOpenAI(model="gpt-4o", http_socket_options=())
    assert recorded
    assert all(opts == () for _, _, opts in recorded)

    # (3) Populated sequence -> verbatim passthrough (not filtered).
    recorded.clear()
    ChatOpenAI(
        model="gpt-4o",
        http_socket_options=[(SOL_SOCKET, SO_KEEPALIVE, 1)],
    )
    assert recorded
    for _, _, opts in recorded:
        assert opts == ((SOL_SOCKET, SO_KEEPALIVE, 1),)