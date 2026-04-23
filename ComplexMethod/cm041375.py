def test_lifespan_listener(serve_asgi_adapter):
    events = Queue()

    @Request.application
    def app(request: Request) -> Response:
        events.put("request")
        return Response("ok", 200)

    class LifespanListener(ASGILifespanListener):
        def on_startup(self):
            events.put("startup")

        def on_shutdown(self):
            events.put("shutdown")

    listener = LifespanListener()

    server = serve_asgi_adapter(app, listener)

    assert events.get(timeout=5) == "startup"
    assert events.qsize() == 0

    assert requests.get(server.url).ok

    assert events.get(timeout=5) == "request"
    assert events.qsize() == 0

    server.shutdown()

    assert events.get(timeout=5) == "shutdown"
    assert events.qsize() == 0