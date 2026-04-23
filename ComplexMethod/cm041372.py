def test_with_werkzeug(self):
        # setup up router
        router = Router()

        def index(_: Request, args) -> Response:
            return Response(b"index")

        def echo_json(request: Request, args) -> Response:
            response = Response()
            response.set_json(request.json)
            return response

        def users(_: Request, args) -> Response:
            response = Response()
            response.set_json(args)
            return response

        router.add("/", index)
        router.add("/users/<int:user_id>", users, host="<host>:<port>")
        router.add("/echo/", echo_json, methods=["POST"])

        # serve router through werkzeug
        @werkzeug.Request.application
        def app(request: werkzeug.Request) -> werkzeug.Response:
            return router.dispatch(request)

        host = "localhost"
        port = get_free_tcp_port()
        url = f"http://{host}:{port}"

        server = werkzeug.serving.make_server(host, port, app=app, threaded=True)
        t = threading.Thread(target=server.serve_forever)
        t.start()

        try:
            resp = requests.get(f"{url}/")
            assert resp.ok
            assert resp.content == b"index"

            resp = requests.get(f"{url}/users/123")
            assert resp.ok
            assert resp.json() == {"user_id": 123, "host": host, "port": str(port)}

            resp = requests.get(f"{url}/users")
            assert not resp.ok

            resp = requests.post(f"{url}/echo", json={"foo": "bar", "a": 420})
            assert resp.ok
            assert resp.json() == {"foo": "bar", "a": 420}
        finally:
            server.shutdown()
            t.join(timeout=10)