async def test_forward_range_header_for_logs(
    hassio_client: TestClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that we forward the Range header for logs."""
    aioclient_mock.get("http://127.0.0.1/host/logs")
    aioclient_mock.get("http://127.0.0.1/host/logs/boots/-1")
    aioclient_mock.get("http://127.0.0.1/host/logs/boots/-2/follow?lines=100")
    aioclient_mock.get("http://127.0.0.1/addons/123abc_esphome/logs")
    aioclient_mock.get("http://127.0.0.1/addons/123abc_esphome/logs/follow")
    aioclient_mock.get("http://127.0.0.1/backups/1234abcd/download")

    test_range = ":-100:50"

    host_resp = await hassio_client.get(
        "/api/hassio/host/logs", headers={"Range": test_range}
    )
    host_resp2 = await hassio_client.get(
        "/api/hassio/host/logs/boots/-1", headers={"Range": test_range}
    )
    host_resp3 = await hassio_client.get(
        "/api/hassio/host/logs/boots/-2/follow?lines=100", headers={"Range": test_range}
    )
    addon_resp = await hassio_client.get(
        "/api/hassio/addons/123abc_esphome/logs", headers={"Range": test_range}
    )
    addon_resp2 = await hassio_client.get(
        "/api/hassio/addons/123abc_esphome/logs/follow", headers={"Range": test_range}
    )
    backup_resp = await hassio_client.get(
        "/api/hassio/backups/1234abcd/download", headers={"Range": test_range}
    )

    assert host_resp.status == HTTPStatus.OK
    assert host_resp2.status == HTTPStatus.OK
    assert host_resp3.status == HTTPStatus.OK
    assert addon_resp.status == HTTPStatus.OK
    assert addon_resp2.status == HTTPStatus.OK
    assert backup_resp.status == HTTPStatus.OK

    assert len(aioclient_mock.mock_calls) == 6

    assert aioclient_mock.mock_calls[0][-1].get("Range") == test_range
    assert aioclient_mock.mock_calls[1][-1].get("Range") == test_range
    assert aioclient_mock.mock_calls[2][-1].get("Range") == test_range
    assert aioclient_mock.mock_calls[3][-1].get("Range") == test_range
    assert aioclient_mock.mock_calls[4][-1].get("Range") == test_range
    assert aioclient_mock.mock_calls[5][-1].get("Range") is None