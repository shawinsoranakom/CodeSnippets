async def test_ssl_refresher():
    ssl_context = MockSSLContext()
    key_path = create_file()
    cert_path = create_file()
    ca_path = create_file()
    ssl_refresher = SSLCertRefresher(ssl_context, key_path, cert_path, ca_path)
    await asyncio.sleep(1)
    assert ssl_context.load_cert_chain_count == 0
    assert ssl_context.load_ca_count == 0

    touch_file(key_path)
    await asyncio.sleep(1)
    assert ssl_context.load_cert_chain_count == 1
    assert ssl_context.load_ca_count == 0

    touch_file(cert_path)
    touch_file(ca_path)
    await asyncio.sleep(1)
    assert ssl_context.load_cert_chain_count == 2
    assert ssl_context.load_ca_count == 1

    ssl_refresher.stop()

    touch_file(cert_path)
    touch_file(ca_path)
    await asyncio.sleep(1)
    assert ssl_context.load_cert_chain_count == 2
    assert ssl_context.load_ca_count == 1