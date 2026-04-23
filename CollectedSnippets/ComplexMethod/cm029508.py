def test_make_response_with_response_instance(app, req_ctx):
    rv = flask.make_response(flask.jsonify({"msg": "W00t"}), 400)
    assert rv.status_code == 400
    assert rv.data == b'{"msg":"W00t"}\n'
    assert rv.mimetype == "application/json"

    rv = flask.make_response(flask.Response(""), 400)
    assert rv.status_code == 400
    assert rv.data == b""
    assert rv.mimetype == "text/html"

    rv = flask.make_response(
        flask.Response("", headers={"Content-Type": "text/html"}),
        400,
        [("X-Foo", "bar")],
    )
    assert rv.status_code == 400
    assert rv.headers["Content-Type"] == "text/html"
    assert rv.headers["X-Foo"] == "bar"