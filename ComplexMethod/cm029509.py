def test_server_name_matching(
    subdomain_matching: bool,
    host_matching: bool,
    expect_subdomain: str,
    expect_host: str,
) -> None:
    app = flask.Flask(
        __name__,
        subdomain_matching=subdomain_matching,
        host_matching=host_matching,
        static_host="example.test" if host_matching else None,
    )
    app.config["SERVER_NAME"] = "example.test"

    @app.route("/", defaults={"name": "default"}, host="<name>")
    @app.route("/", subdomain="<name>", host="<name>.example.test")
    def index(name: str) -> str:
        return name

    client = app.test_client()

    r = client.get(base_url="http://example.test")
    assert r.text == "default"

    r = client.get(base_url="http://abc.example.test")
    assert r.text == expect_subdomain

    with pytest.warns() if subdomain_matching else nullcontext():
        r = client.get(base_url="http://xyz.other.test")

        if werkzeug_3_2:
            assert r.text == "default"
        else:
            assert r.text == expect_host