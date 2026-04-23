def test_broken_scope() -> None:
    with pytest.raises(
        FastAPIError,
        match='The dependency "get_named_func_session" has a scope of "request", it cannot depend on dependencies with scope "function"',
    ):

        @app.websocket("/broken-scope")
        async def get_broken(
            websocket: WebSocket, sessions: BrokenSessionsDep
        ) -> Any:  # pragma: no cover
            pass