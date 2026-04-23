def test_robust_teardown(app: flask.Flask, client: FlaskClient) -> None:
    count = 0

    @app.teardown_request
    def request_teardown(e: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("request_teardown")

    @app.teardown_appcontext
    def app_teardown(e: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("app_teardown")

    @app.get("/")
    def index() -> str:
        return ""

    def request_signal(sender: flask.Flask, exc: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("request_signal")

    def app_signal(sender: flask.Flask, exc: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("app_signal")

    with (
        flask.request_tearing_down.connected_to(request_signal, app),
        flask.appcontext_tearing_down.connected_to(app_signal, app),
    ):
        if sys.version_info >= (3, 11):
            with pytest.raises(ExceptionGroup, match="context teardown") as exc_info:  # noqa: F821
                client.get()

            assert len(exc_info.value.exceptions) == 2
            eg1, eg2 = exc_info.value.exceptions
            assert isinstance(eg1, ExceptionGroup)  # noqa: F821
            assert "request teardown" in eg1.message
            assert len(eg1.exceptions) == 2
            assert isinstance(eg2, ExceptionGroup)  # noqa: F821
            assert "app teardown" in eg2.message
            assert len(eg2.exceptions) == 2
        else:
            with pytest.raises(ValueError, match="request_teardown"):
                client.get()

    assert count == 4