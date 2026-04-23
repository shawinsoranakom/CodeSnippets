async def test_referer_policies_setting():
    crawler = get_crawler(
        settings_dict={
            "REFERRER_POLICY": "no-referrer",
            "REFERRER_POLICIES": {
                "no-referrer-when-downgrade": None,
                "custom-policy": CustomPythonOrgPolicy,
                "": CustomPythonOrgPolicy,
            },
        }
    )
    mw = build_from_crawler(RefererMiddleware, crawler)

    async def input_result():
        yield Request("https://example.com/")

    # "no-referrer-when-downgrade": None,
    response = Response(
        "https://example.com/",
        headers={"Referrer-Policy": "no-referrer-when-downgrade"},
    )
    with pytest.warns(
        RuntimeWarning,
        match=r"Could not load referrer policy 'no-referrer-when-downgrade'",
    ):
        output = [
            request
            async for request in mw.process_spider_output_async(
                response, input_result()
            )
        ]
    assert len(output) == 1
    assert b"Referer" not in output[0].headers

    # "custom-policy": CustomPythonOrgPolicy,
    response = Response(
        "https://example.com/",
        headers={"Referrer-Policy": "custom-policy"},
    )
    output = [
        request
        async for request in mw.process_spider_output_async(response, input_result())
    ]
    assert len(output) == 1
    assert output[0].headers == {b"Referer": [b"https://python.org/"]}

    # "": CustomPythonOrgPolicy,
    response = Response(
        "https://example.com/",
        headers={"Referrer-Policy": ""},
    )
    output = [
        request
        async for request in mw.process_spider_output_async(response, input_result())
    ]
    assert len(output) == 1
    assert output[0].headers == {b"Referer": [b"https://python.org/"]}