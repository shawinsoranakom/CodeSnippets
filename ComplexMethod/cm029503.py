def test_session_expiration(app, client):
    permanent = True

    @app.route("/")
    def index():
        flask.session["test"] = 42
        flask.session.permanent = permanent
        return ""

    @app.route("/test")
    def test():
        return str(flask.session.permanent)

    rv = client.get("/")
    assert "set-cookie" in rv.headers
    match = re.search(r"(?i)\bexpires=([^;]+)", rv.headers["set-cookie"])
    expires = parse_date(match.group())
    expected = datetime.now(timezone.utc) + app.permanent_session_lifetime
    assert expires.year == expected.year
    assert expires.month == expected.month
    assert expires.day == expected.day

    rv = client.get("/test")
    assert rv.data == b"True"

    permanent = False
    rv = client.get("/")
    assert "set-cookie" in rv.headers
    match = re.search(r"\bexpires=([^;]+)", rv.headers["set-cookie"])
    assert match is None