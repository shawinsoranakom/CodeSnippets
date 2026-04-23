def test_post_form_urlencoded_and_query():
    # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST#example
    r = Request(
        "POST",
        "/form",
        query_string="query1=foo&query2=bar",
        body=b"field1=value1&field2=value2",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert len(r.form) == 2
    assert r.form["field1"] == "value1"
    assert r.form["field2"] == "value2"

    assert len(r.args) == 2
    assert r.args["query1"] == "foo"
    assert r.args["query2"] == "bar"

    assert len(r.values) == 4
    assert r.values["field1"] == "value1"
    assert r.values["field2"] == "value2"
    assert r.args["query1"] == "foo"
    assert r.args["query2"] == "bar"