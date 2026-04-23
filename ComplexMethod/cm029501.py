def test_session_accessed(app: flask.Flask, client: FlaskClient) -> None:
    @app.post("/")
    def do_set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.get("/")
    def do_get():
        return flask.session.get("value", "None")

    @app.get("/nothing")
    def do_nothing() -> str:
        return ""

    with client:
        rv = client.get("/nothing")
        assert "cookie" not in rv.vary
        assert not app_ctx._session.accessed
        assert not app_ctx._session.modified

    with client:
        rv = client.post(data={"value": "42"})
        assert rv.text == "value set"
        assert "cookie" in rv.vary
        assert app_ctx._session.accessed
        assert app_ctx._session.modified

    with client:
        rv = client.get()
        assert rv.text == "42"
        assert "cookie" in rv.vary
        assert app_ctx._session.accessed
        assert not app_ctx._session.modified

    with client:
        rv = client.get("/nothing")
        assert rv.text == ""
        assert "cookie" not in rv.vary
        assert not app_ctx._session.accessed
        assert not app_ctx._session.modified