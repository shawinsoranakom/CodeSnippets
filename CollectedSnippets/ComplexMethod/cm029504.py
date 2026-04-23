def test_session_special_types(app, client):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    the_uuid = uuid.uuid4()

    @app.route("/")
    def dump_session_contents():
        flask.session["t"] = (1, 2, 3)
        flask.session["b"] = b"\xff"
        flask.session["m"] = Markup("<html>")
        flask.session["u"] = the_uuid
        flask.session["d"] = now
        flask.session["t_tag"] = {" t": "not-a-tuple"}
        flask.session["di_t_tag"] = {" t__": "not-a-tuple"}
        flask.session["di_tag"] = {" di": "not-a-dict"}
        return "", 204

    with client:
        client.get("/")
        s = flask.session
        assert s["t"] == (1, 2, 3)
        assert type(s["b"]) is bytes  # noqa: E721
        assert s["b"] == b"\xff"
        assert type(s["m"]) is Markup  # noqa: E721
        assert s["m"] == Markup("<html>")
        assert s["u"] == the_uuid
        assert s["d"] == now
        assert s["t_tag"] == {" t": "not-a-tuple"}
        assert s["di_t_tag"] == {" t__": "not-a-tuple"}
        assert s["di_tag"] == {" di": "not-a-dict"}