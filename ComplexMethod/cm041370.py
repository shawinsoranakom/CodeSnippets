def test_path_converter(self):
        router = Router()
        router.add(path="/<path:path>", endpoint=echo_params_json)

        assert router.dispatch(Request(path="/my")).json == {"path": "my"}
        assert router.dispatch(Request(path="/my/")).json == {"path": "my/"}
        assert router.dispatch(Request(path="/my//path")).json == {"path": "my//path"}
        assert router.dispatch(Request(path="/my//path/")).json == {"path": "my//path/"}
        assert router.dispatch(Request(path="/my/path foobar")).json == {"path": "my/path foobar"}
        assert router.dispatch(Request(path="//foobar")).json == {"path": "foobar"}
        assert router.dispatch(Request(path="//foobar/")).json == {"path": "foobar/"}