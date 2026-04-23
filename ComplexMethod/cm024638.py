async def test_setup_config_entry_dynamic_instances(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test dynamic changes in the instance configuration."""
    config_entry = add_test_config_entry(hass)

    master_client = create_mock_client()
    master_client.instances = [TEST_INSTANCE_1, TEST_INSTANCE_2]

    entity_client = create_mock_client()
    entity_client.instances = master_client.instances

    with patch(
        "homeassistant.components.hyperion.client.HyperionClient",
        side_effect=[master_client, entity_client, entity_client],
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get(TEST_ENTITY_ID_1) is not None
    assert hass.states.get(TEST_ENTITY_ID_2) is not None

    assert master_client.set_callbacks.called

    # == Inject a new instances update (stop instance 1, add instance 3)
    instance_callback = master_client.set_callbacks.call_args[0][0][
        f"{const.KEY_INSTANCE}-{const.KEY_UPDATE}"
    ]

    with patch(
        "homeassistant.components.hyperion.client.HyperionClient",
        return_value=entity_client,
    ):
        await instance_callback(
            {
                const.KEY_SUCCESS: True,
                const.KEY_DATA: [
                    {**TEST_INSTANCE_1, "running": False},
                    TEST_INSTANCE_2,
                    TEST_INSTANCE_3,
                ],
            }
        )
        await hass.async_block_till_done()

    assert hass.states.get(TEST_ENTITY_ID_1) is None
    assert hass.states.get(TEST_ENTITY_ID_2) is not None
    assert hass.states.get(TEST_ENTITY_ID_3) is not None

    # Instance 1 is stopped, it should still be registered.
    assert entity_registry.async_is_registered(TEST_ENTITY_ID_1)

    # == Inject a new instances update (remove instance 1)
    assert master_client.set_callbacks.called
    instance_callback = master_client.set_callbacks.call_args[0][0][
        f"{const.KEY_INSTANCE}-{const.KEY_UPDATE}"
    ]
    with patch(
        "homeassistant.components.hyperion.client.HyperionClient",
        return_value=entity_client,
    ):
        await instance_callback(
            {
                const.KEY_SUCCESS: True,
                const.KEY_DATA: [TEST_INSTANCE_2, TEST_INSTANCE_3],
            }
        )
        await hass.async_block_till_done()

    assert hass.states.get(TEST_ENTITY_ID_1) is None
    assert hass.states.get(TEST_ENTITY_ID_2) is not None
    assert hass.states.get(TEST_ENTITY_ID_3) is not None

    # Instance 1 is removed, it should not still be registered.
    assert not entity_registry.async_is_registered(TEST_ENTITY_ID_1)

    # == Inject a new instances update (re-add instance 1, but not running)
    with patch(
        "homeassistant.components.hyperion.client.HyperionClient",
        return_value=entity_client,
    ):
        await instance_callback(
            {
                const.KEY_SUCCESS: True,
                const.KEY_DATA: [
                    {**TEST_INSTANCE_1, "running": False},
                    TEST_INSTANCE_2,
                    TEST_INSTANCE_3,
                ],
            }
        )
        await hass.async_block_till_done()

    assert hass.states.get(TEST_ENTITY_ID_1) is None
    assert hass.states.get(TEST_ENTITY_ID_2) is not None
    assert hass.states.get(TEST_ENTITY_ID_3) is not None

    # == Inject a new instances update (re-add instance 1, running)
    with patch(
        "homeassistant.components.hyperion.client.HyperionClient",
        return_value=entity_client,
    ):
        await instance_callback(
            {
                const.KEY_SUCCESS: True,
                const.KEY_DATA: [TEST_INSTANCE_1, TEST_INSTANCE_2, TEST_INSTANCE_3],
            }
        )
        await hass.async_block_till_done()

    assert hass.states.get(TEST_ENTITY_ID_1) is not None
    assert hass.states.get(TEST_ENTITY_ID_2) is not None
    assert hass.states.get(TEST_ENTITY_ID_3) is not None