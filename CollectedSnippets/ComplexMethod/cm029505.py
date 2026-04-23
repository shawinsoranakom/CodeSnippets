def test_trap_bad_request_key_error(app, client, debug, trap, expect_key, expect_abort):
    app.config["DEBUG"] = debug
    app.config["TRAP_BAD_REQUEST_ERRORS"] = trap

    @app.route("/key")
    def fail():
        flask.request.form["missing_key"]

    @app.route("/abort")
    def allow_abort():
        flask.abort(400)

    if expect_key:
        rv = client.get("/key")
        assert rv.status_code == 400
        assert b"missing_key" not in rv.data
    else:
        with pytest.raises(KeyError) as exc_info:
            client.get("/key")

        assert exc_info.errisinstance(BadRequest)
        assert "missing_key" in exc_info.value.get_description()

    if expect_abort:
        rv = client.get("/abort")
        assert rv.status_code == 400
    else:
        with pytest.raises(BadRequest):
            client.get("/abort")