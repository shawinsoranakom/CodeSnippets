async def test_default_engine_prefer_cloud_entity(
    hass: HomeAssistant,
    tmp_path: Path,
    mock_provider: MockSTTProvider,
    config_flow_test_domains: str,
) -> None:
    """Test async_default_engine.

    In this tests there's an entity from domain cloud, an entity from domain new_test
    and a legacy provider.
    The test asserts async_default_engine returns the entity from domain cloud.
    """
    await mock_setup(hass, tmp_path, mock_provider)
    for domain in config_flow_test_domains:
        entity = MockSTTProviderEntity()
        entity.url_path = f"stt.{domain}"
        entity._attr_name = f"{domain} STT entity"
        await mock_config_entry_setup(hass, tmp_path, entity, test_domain=domain)
    await hass.async_block_till_done()

    for domain in config_flow_test_domains:
        entity_engine = async_get_speech_to_text_engine(
            hass, f"stt.{domain}_stt_entity"
        )
        assert entity_engine is not None
        assert entity_engine.name == f"{domain} STT entity"

    provider_engine = async_get_speech_to_text_engine(hass, "test")
    assert provider_engine is not None
    assert provider_engine.name == "test"
    assert async_default_engine(hass) == "stt.cloud_stt_entity"