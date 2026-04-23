def test_session_using_session_settings(app, client):
    app.config.update(
        SERVER_NAME="www.example.com:8080",
        APPLICATION_ROOT="/test",
        SESSION_COOKIE_DOMAIN=".example.com",
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_PARTITIONED=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_PATH="/",
    )

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    @app.route("/clear")
    def clear():
        flask.session.pop("testing", None)
        return "Goodbye World"

    rv = client.get("/", "http://www.example.com:8080/test/")
    cookie = rv.headers["set-cookie"].lower()
    # or condition for Werkzeug < 2.3
    assert "domain=example.com" in cookie or "domain=.example.com" in cookie
    assert "path=/" in cookie
    assert "secure" in cookie
    assert "httponly" not in cookie
    assert "samesite" in cookie
    assert "partitioned" in cookie

    rv = client.get("/clear", "http://www.example.com:8080/test/")
    cookie = rv.headers["set-cookie"].lower()
    assert "session=;" in cookie
    # or condition for Werkzeug < 2.3
    assert "domain=example.com" in cookie or "domain=.example.com" in cookie
    assert "path=/" in cookie
    assert "secure" in cookie
    assert "samesite" in cookie
    assert "partitioned" in cookie