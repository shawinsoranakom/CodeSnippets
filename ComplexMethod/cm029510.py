def test_server_name_subdomain():
    app = flask.Flask(__name__, subdomain_matching=True)
    client = app.test_client()

    @app.route("/")
    def index():
        return "default"

    @app.route("/", subdomain="foo")
    def subdomain():
        return "subdomain"

    app.config["SERVER_NAME"] = "dev.local:5000"
    rv = client.get("/")
    assert rv.data == b"default"

    rv = client.get("/", "http://dev.local:5000")
    assert rv.data == b"default"

    rv = client.get("/", "https://dev.local:5000")
    assert rv.data == b"default"

    app.config["SERVER_NAME"] = "dev.local:443"
    rv = client.get("/", "https://dev.local")

    # Werkzeug 1.0 fixes matching https scheme with 443 port
    if rv.status_code != 404:
        assert rv.data == b"default"

    app.config["SERVER_NAME"] = "dev.local"
    rv = client.get("/", "https://dev.local")
    assert rv.data == b"default"

    with pytest.warns(match="Current server name"):
        rv = client.get("/", "http://foo.localhost")

    if werkzeug_3_2:
        assert rv.status_code == 200
    else:
        assert rv.status_code == 404

    rv = client.get("/", "http://foo.dev.local")
    assert rv.data == b"subdomain"