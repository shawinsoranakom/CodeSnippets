async def test_service_person(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Set up component, test person services."""
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups"),
        text=await async_load_fixture(hass, "persongroups.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group2/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )

    with assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    assert len(aioclient_mock.mock_calls) == 3

    aioclient_mock.post(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "create_person.json", DOMAIN),
    )
    aioclient_mock.delete(
        ENDPOINT_URL.format(
            "persongroups/test_group1/persons/25985303-c537-4467-b41d-bdb45cd95ca1"
        ),
        status=200,
        text="{}",
    )

    create_person(hass, "test group1", "Hans")
    await hass.async_block_till_done()

    entity_group1 = hass.states.get("microsoft_face.test_group1")

    assert len(aioclient_mock.mock_calls) == 4
    assert entity_group1 is not None
    assert entity_group1.attributes["Hans"] == "25985303-c537-4467-b41d-bdb45cd95ca1"

    delete_person(hass, "test group1", "Hans")
    await hass.async_block_till_done()

    entity_group1 = hass.states.get("microsoft_face.test_group1")

    assert len(aioclient_mock.mock_calls) == 5
    assert entity_group1 is not None
    assert "Hans" not in entity_group1.attributes