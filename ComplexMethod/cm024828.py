async def test_trigger_no_availability_template(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test manual trigger template entity when availability template isn't used."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ICON: template.Template(_ICON_TEMPLATE, hass),
        CONF_PICTURE: template.Template(_PICTURE_TEMPLATE, hass),
        CONF_STATE: template.Template("{{ value == 'on' }}", hass),
    }

    class TestEntity(ManualTriggerEntity):
        """Test entity class."""

        extra_template_keys = (CONF_STATE,)

        @property
        def state(self) -> bool | None:
            """Return extra attributes."""
            return self._rendered.get(CONF_STATE)

    entity = TestEntity(hass, config)
    entity.entity_id = "test.entity"
    variables = entity._template_variables_with_value(STATE_ON)
    assert entity._render_availability_template(variables) is True
    assert entity.available is True
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    assert entity.state == "True"
    assert entity.icon == "mdi:on"
    assert entity.entity_picture == "/local/picture_on"

    variables = entity._template_variables_with_value(STATE_OFF)
    assert entity._render_availability_template(variables) is True
    assert entity.available is True
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    assert entity.state == "False"
    assert entity.icon == "mdi:off"
    assert entity.entity_picture == "/local/picture_off"