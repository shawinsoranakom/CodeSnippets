def test_resource_decorator_dispatches_correctly(self):
        router = Router(dispatcher=handler_dispatcher())

        requests = []

        @resource("/_localstack/health")
        class TestResource:
            def on_get(self, req):
                requests.append(req)
                return "GET/OK"

            def on_post(self, req):
                requests.append(req)
                return {"ok": "POST"}

            def on_head(self, req):
                # this is ignored
                requests.append(req)
                return "HEAD/OK"

        router.add(TestResource())

        request1 = Request("GET", "/_localstack/health")
        request2 = Request("POST", "/_localstack/health")
        request3 = Request("HEAD", "/_localstack/health")
        assert router.dispatch(request1).get_data(True) == "GET/OK"
        assert router.dispatch(request1).get_data(True) == "GET/OK"
        assert router.dispatch(request2).json == {"ok": "POST"}
        assert router.dispatch(request3).get_data(True) == "HEAD/OK"
        assert len(requests) == 4
        assert requests[0] is request1
        assert requests[1] is request1
        assert requests[2] is request2
        assert requests[3] is request3