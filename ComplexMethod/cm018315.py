async def test_browse_media(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test Jellyfin browse media."""
    client = await hass_ws_client()

    # browse root folder
    await client.send_json(
        {
            "id": 1,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expected_child_item = {
        "title": "COLLECTION FOLDER",
        "media_class": MediaClass.DIRECTORY.value,
        "media_content_type": "collection",
        "media_content_id": "COLLECTION-FOLDER-UUID",
        "can_play": False,
        "can_expand": True,
        "can_search": False,
        "thumbnail": "http://localhost/Items/c22fd826-17fc-44f4-9b04-1eb3e8fb9173/Images/Backdrop.jpg",
        "children_media_class": None,
    }

    assert response["result"]["media_content_id"] == ""
    assert response["result"]["media_content_type"] == "root"
    assert response["result"]["title"] == "Jellyfin"
    assert response["result"]["children"][0] == expected_child_item

    # browse collection folder
    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "collection",
            "media_content_id": "COLLECTION-FOLDER-UUID",
        }
    )

    response = await client.receive_json()
    expected_child_item = {
        "title": "EPISODE",
        "media_class": MediaClass.EPISODE.value,
        "media_content_type": MediaType.EPISODE.value,
        "media_content_id": "EPISODE-UUID",
        "can_play": True,
        "can_expand": False,
        "can_search": False,
        "thumbnail": "http://localhost/Items/21af9851-8e39-43a9-9c47-513d3b9e99fc/Images/Primary.jpg",
        "children_media_class": None,
    }

    assert response["success"]
    assert response["result"]["media_content_id"] == "COLLECTION-FOLDER-UUID"
    assert response["result"]["title"] == "FOLDER"
    assert response["result"]["children"][0] == expected_child_item

    # browse for series
    await client.send_json(
        {
            "id": 3,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "tvshow",
            "media_content_id": "SERIES-UUID",
        }
    )

    response = await client.receive_json()
    expected_child_item = {
        "title": "SEASON",
        "media_class": MediaClass.SEASON.value,
        "media_content_type": MediaType.SEASON.value,
        "media_content_id": "SEASON-UUID",
        "can_play": True,
        "can_expand": True,
        "can_search": False,
        "thumbnail": "http://localhost/Items/c22fd826-17fc-44f4-9b04-1eb3e8fb9173/Images/Backdrop.jpg",
        "children_media_class": None,
    }

    assert response["success"]
    assert response["result"]["media_content_id"] == "SERIES-UUID"
    assert response["result"]["title"] == "SERIES"
    assert response["result"]["children"][0] == expected_child_item

    # browse for season
    await client.send_json(
        {
            "id": 4,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "season",
            "media_content_id": "SEASON-UUID",
        }
    )

    response = await client.receive_json()
    expected_child_item = {
        "title": "EPISODE",
        "media_class": MediaClass.EPISODE.value,
        "media_content_type": MediaType.EPISODE.value,
        "media_content_id": "EPISODE-UUID",
        "can_play": True,
        "can_expand": False,
        "can_search": False,
        "thumbnail": "http://localhost/Items/21af9851-8e39-43a9-9c47-513d3b9e99fc/Images/Primary.jpg",
        "children_media_class": None,
    }

    assert response["success"]
    assert response["result"]["media_content_id"] == "SEASON-UUID"
    assert response["result"]["title"] == "SEASON"
    assert response["result"]["children"][0] == expected_child_item

    # browse for collection without children
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = {}

    await client.send_json(
        {
            "id": 5,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "collection",
            "media_content_id": "COLLECTION-FOLDER-UUID",
        }
    )

    response = await client.receive_json()
    assert response["success"] is False
    assert response["error"]
    assert response["error"]["message"] == "Media not found: COLLECTION-FOLDER-UUID"

    # browse for non-existent item
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = {}

    await client.send_json(
        {
            "id": 6,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "collection",
            "media_content_id": "COLLECTION-UUID-404",
        }
    )

    response = await client.receive_json()
    assert response["success"] is False
    assert response["error"]
    assert response["error"]["message"] == "Media not found: COLLECTION-UUID-404"