async def test_custom_wake_words(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test exposing custom wake word models.

    Expects 2 models in testing_config/custom_wake_words:
    - hey_home_assistant
    - choo_choo_homie
    """
    http_client = await hass_client()
    expected_config = AssistSatelliteConfiguration(
        available_wake_words=[
            AssistSatelliteWakeWord("1234", "okay nabu", ["en"]),
        ],
        active_wake_words=["1234"],
        max_active_wake_words=1,
    )
    gvac = mock_client.get_voice_assistant_configuration
    gvac.return_value = expected_config

    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={
            "voice_assistant_feature_flags": VoiceAssistantFeature.VOICE_ASSISTANT
            | VoiceAssistantFeature.ANNOUNCE
        },
    )
    await hass.async_block_till_done()

    satellite = get_satellite_entity(hass, mock_device.device_info.mac_address)
    assert satellite is not None

    # Models should be present in testing_config/custom_wake_words
    gvac.assert_called_once()
    external_wake_words = gvac.call_args_list[0].kwargs["external_wake_words"]
    assert len(external_wake_words) == 2

    assert {external_wake_words[0].id, external_wake_words[1].id} == {
        "hey_home_assistant",
        "choo_choo_homie",
    }

    # Verify details
    for eww in external_wake_words:
        if eww.id == "hey_home_assistant":
            assert eww.wake_word == "Hey Home Assistant"
        else:
            assert eww.wake_word == "Choo Choo Homie"

        assert eww.model_type == "micro"
        assert eww.model_size == 4  # tflite files contain "test"
        assert (
            eww.model_hash
            == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        )
        assert eww.trained_languages == ["en"]

        # GET config
        config_url = eww.url[eww.url.find("/api") :]
        req = await http_client.get(config_url)
        assert req.status == HTTPStatus.OK
        config_dict = await req.json()

        # GET model
        model = config_dict["model"]
        model_url = config_url[: config_url.rfind("/")] + f"/{model}"
        req = await http_client.get(model_url)
        assert req.status == HTTPStatus.OK

    # Check non-existent wake word
    req = await http_client.get("/api/esphome/wake_words/wrong_wake_word.json")
    assert req.status == HTTPStatus.NOT_FOUND