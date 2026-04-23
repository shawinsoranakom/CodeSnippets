def test_serve_multiple_apps(serve_asgi_adapter):
    @Request.application
    def app0(request: Request) -> Response:
        return Response("ok0", 200)

    @Request.application
    def app1(request: Request) -> Response:
        return Response("ok1", 200)

    server0 = serve_asgi_adapter(app0)
    server1 = serve_asgi_adapter(app1)

    executor = ThreadPoolExecutor(6)

    response0_ftr = executor.submit(requests.get, server0.url)
    response1_ftr = executor.submit(requests.get, server1.url)
    response2_ftr = executor.submit(requests.get, server0.url)
    response3_ftr = executor.submit(requests.get, server1.url)
    response4_ftr = executor.submit(requests.get, server0.url)
    response5_ftr = executor.submit(requests.get, server1.url)

    executor.shutdown()

    result0 = response0_ftr.result(timeout=2)
    assert result0.ok
    assert result0.text == "ok0"
    result1 = response1_ftr.result(timeout=2)
    assert result1.ok
    assert result1.text == "ok1"
    result2 = response2_ftr.result(timeout=2)
    assert result2.ok
    assert result2.text == "ok0"
    result3 = response3_ftr.result(timeout=2)
    assert result3.ok
    assert result3.text == "ok1"
    result4 = response4_ftr.result(timeout=2)
    assert result4.ok
    assert result4.text == "ok0"
    result5 = response5_ftr.result(timeout=2)
    assert result5.ok
    assert result5.text == "ok1"