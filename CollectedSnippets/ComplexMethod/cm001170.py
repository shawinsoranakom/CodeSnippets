async def test_large_header_handling():
    """Test that ClientSession with max_field_size=16384 can handle large headers (>8190 bytes)"""
    import aiohttp

    # Create a test server that returns large headers
    async def large_header_handler(request):
        # Create a header value larger than the default aiohttp max_field_size (8190 bytes)
        # Simulate a long CSP header or similar legitimate large header
        large_value = "policy-" + "x" * 8500
        return web.Response(
            text="OK",
            headers={"X-Large-Header": large_value},
        )

    app = web.Application()
    app.router.add_get("/large-header", large_header_handler)

    # Start test server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    try:
        # Get the port from the server
        server = site._server
        assert server is not None
        sockets = getattr(server, "sockets", None)
        assert sockets is not None
        port = sockets[0].getsockname()[1]

        # Test with default max_field_size (should fail)
        default_failed = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{port}/large-header") as resp:
                    await resp.read()
        except Exception:
            # Expected: any error with default settings when header > 8190 bytes
            default_failed = True

        assert default_failed, "Expected error with default max_field_size"

        # Test with increased max_field_size (should succeed)
        # This is the fix: setting max_field_size=16384 allows headers up to 16KB
        async with aiohttp.ClientSession(max_field_size=16384) as session:
            async with session.get(f"http://127.0.0.1:{port}/large-header") as resp:
                body = await resp.read()
                # Verify the response is successful
                assert resp.status == 200
                assert "X-Large-Header" in resp.headers
                # Verify the large header value was received
                assert len(resp.headers["X-Large-Header"]) > 8190
                assert body == b"OK"

    finally:
        await runner.cleanup()