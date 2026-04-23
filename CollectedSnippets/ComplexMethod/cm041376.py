def app(request: Request) -> Response:
        assert request.stream.read(1) == b"f"
        assert request.stream.readline(10) == b"ood\n"
        assert request.stream.readline(3) == b"bar"
        assert next(request.stream) == b"ber\n"
        assert request.stream.readlines(3) == [b"fizz\n"]
        assert request.stream.readline() == b"buzz\n"
        assert request.stream.read() == b"really\ndone"
        assert request.stream.read(10) == b""

        return Response("ok", 200)