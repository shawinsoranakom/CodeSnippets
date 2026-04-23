def test_make_response(app, req_ctx):
    rv = flask.make_response()
    assert rv.status_code == 200
    assert rv.data == b""
    assert rv.mimetype == "text/html"

    rv = flask.make_response("Awesome")
    assert rv.status_code == 200
    assert rv.data == b"Awesome"
    assert rv.mimetype == "text/html"

    rv = flask.make_response("W00t", 404)
    assert rv.status_code == 404
    assert rv.data == b"W00t"
    assert rv.mimetype == "text/html"

    rv = flask.make_response(c for c in "Hello")
    assert rv.status_code == 200
    assert rv.data == b"Hello"
    assert rv.mimetype == "text/html"