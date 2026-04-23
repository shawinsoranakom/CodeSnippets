async def test_setup_component_test_entities(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Set up component."""
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

    entity_group1 = hass.states.get("microsoft_face.test_group1")
    entity_group2 = hass.states.get("microsoft_face.test_group2")

    assert entity_group1 is not None
    assert entity_group2 is not None

    assert entity_group1.attributes["Ryan"] == "25985303-c537-4467-b41d-bdb45cd95ca1"
    assert entity_group1.attributes["David"] == "2ae4935b-9659-44c3-977f-61fac20d0538"

    assert entity_group2.attributes["Ryan"] == "25985303-c537-4467-b41d-bdb45cd95ca1"
    assert entity_group2.attributes["David"] == "2ae4935b-9659-44c3-977f-61fac20d0538"