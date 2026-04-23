def test_serve_asgi_adapter(serve_asgi_adapter):
    request_list: list[Request] = []

    @Request.application
    def app(request: Request) -> Response:
        request_list.append(request)
        return Response("ok", 200)

    server = serve_asgi_adapter(app)

    response0 = requests.get(server.url + "/foobar?foo=bar", headers={"x-amz-target": "testing"})
    assert response0.ok
    assert response0.text == "ok"

    response1 = requests.get(server.url + "/compute", data='{"foo": "bar"}')
    assert response1.ok
    assert response1.text == "ok"

    request0 = request_list[0]
    assert request0.path == "/foobar"
    assert request0.query_string == b"foo=bar"
    assert request0.full_path == "/foobar?foo=bar"
    assert request0.headers["x-amz-target"] == "testing"
    assert dict(request0.args) == {"foo": "bar"}

    request1 = request_list[1]
    assert request1.path == "/compute"
    assert request1.get_data() == b'{"foo": "bar"}'