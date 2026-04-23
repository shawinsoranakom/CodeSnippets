def test_templates_and_static(test_apps):
    from blueprintapp import app

    client = app.test_client()

    rv = client.get("/")
    assert rv.data == b"Hello from the Frontend"
    rv = client.get("/admin/")
    assert rv.data == b"Hello from the Admin"
    rv = client.get("/admin/index2")
    assert rv.data == b"Hello from the Admin"

    with client.get("/admin/static/test.txt") as rv:
        assert rv.data.strip() == b"Admin File"

    with client.get("/admin/static/css/test.css") as rv:
        assert rv.data.strip() == b"/* nested file */"

    # try/finally, in case other tests use this app for Blueprint tests.
    max_age_default = app.config["SEND_FILE_MAX_AGE_DEFAULT"]
    try:
        expected_max_age = 3600
        if app.config["SEND_FILE_MAX_AGE_DEFAULT"] == expected_max_age:
            expected_max_age = 7200
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = expected_max_age

        with client.get("/admin/static/css/test.css") as rv:
            cc = parse_cache_control_header(rv.headers["Cache-Control"])
            assert cc.max_age == expected_max_age
    finally:
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = max_age_default

    with app.test_request_context():
        assert (
            flask.url_for("admin.static", filename="test.txt")
            == "/admin/static/test.txt"
        )

    with app.test_request_context():
        with pytest.raises(TemplateNotFound) as e:
            flask.render_template("missing.html")
        assert e.value.name == "missing.html"

    with flask.Flask(__name__).test_request_context():
        assert flask.render_template("nested/nested.txt") == "I'm nested"