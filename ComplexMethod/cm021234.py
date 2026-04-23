async def test_ws_list_engines(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup: MockSTTProvider | MockSTTProviderEntity,
    engine_id: str,
    extra_data: dict[str, str],
) -> None:
    """Test listing speech-to-text engines."""
    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "stt/engine/list"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["de", "de-CH", "en"]}
            | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "smurfish"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [{"engine_id": engine_id, "supported_languages": []} | extra_data]
    }

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "en"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["en"]} | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "en-UK"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["en"]} | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "de"})
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["de", "de-CH"]}
            | extra_data
        ]
    }

    await client.send_json_auto_id(
        {"type": "stt/engine/list", "language": "de", "country": "ch"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["de-CH", "de"]}
            | extra_data
        ]
    }