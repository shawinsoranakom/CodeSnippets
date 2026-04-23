async def test_ws_list_engines(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup: str,
    engine_id: str,
    extra_data: dict[str, str],
) -> None:
    """Test listing tts engines and supported languages."""
    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "tts/engine/list"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {
                "engine_id": engine_id,
                "supported_languages": ["de_CH", "de_DE", "en_GB", "en_US"],
            }
            | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "tts/engine/list", "language": "smurfish"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [{"engine_id": engine_id, "supported_languages": []} | extra_data]
    }

    await client.send_json_auto_id({"type": "tts/engine/list", "language": "en"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["en_US", "en_GB"]}
            | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "tts/engine/list", "language": "en-UK"})

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["en_GB", "en_US"]}
            | extra_data
        ]
    }

    await client.send_json_auto_id({"type": "tts/engine/list", "language": "de"})
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["de_DE", "de_CH"]}
            | extra_data
        ]
    }

    await client.send_json_auto_id(
        {"type": "tts/engine/list", "language": "de", "country": "ch"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == {
        "providers": [
            {"engine_id": engine_id, "supported_languages": ["de_CH", "de_DE"]}
            | extra_data
        ]
    }