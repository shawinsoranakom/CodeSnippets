async def test_assist_api_prompt(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test prompt for the assist API."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})
    context = Context()
    llm_context = llm.LLMContext(
        platform="test_platform",
        context=context,
        language="*",
        assistant="conversation",
        device_id=None,
    )
    api = await llm.async_get_api(hass, "assist", llm_context)
    assert api.api_prompt == (
        "Only if the user wants to control a device, tell them to expose entities to their "
        "voice assistant in Home Assistant."
    )

    # Expose entities

    # Create a script with a unique ID
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test_script": {
                    "description": "This is a test script",
                    "sequence": [],
                    "fields": {
                        "beer": {"description": "Number of beers"},
                        "wine": {},
                    },
                },
                "script_with_no_fields": {
                    "description": "This is another test script",
                    "sequence": [],
                },
            }
        },
    )
    async_expose_entity(hass, "conversation", "script.test_script", True)
    async_expose_entity(hass, "conversation", "script.script_with_no_fields", True)

    entry = MockConfigEntry(title=None)
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={("test", "123456")},
        suggested_area="Test Area",
    )
    area = area_registry.async_get_area_by_name("Test Area")
    area_registry.async_update(area.id, aliases=["Alternative name"])
    entry1 = entity_registry.async_get_or_create(
        "light",
        "kitchen",
        "mock-id-kitchen",
        original_name="Kitchen",
        suggested_object_id="kitchen",
    )
    entry2 = entity_registry.async_get_or_create(
        "light",
        "living_room",
        "mock-id-living-room",
        original_name="Living Room",
        suggested_object_id="living_room",
        device_id=device.id,
    )
    hass.states.async_set(
        entry1.entity_id,
        "on",
        {"friendly_name": "Kitchen", "temperature": Decimal("0.9"), "humidity": 65},
    )
    hass.states.async_set(entry2.entity_id, "on", {"friendly_name": "Living Room"})

    def create_entity(
        device: dr.DeviceEntry,
        write_state=True,
        aliases: list[er.AliasEntry] | None = None,
    ) -> None:
        """Create an entity for a device and track entity_id."""
        entity = entity_registry.async_get_or_create(
            "light",
            "test",
            device.id,
            device_id=device.id,
            original_name=str(device.name or "Unnamed Device"),
            suggested_object_id=str(device.name or "unnamed_device"),
        )
        if aliases:
            entity_registry.async_update_entity(entity.entity_id, aliases=aliases)
        if write_state:
            entity.write_unavailable_state(hass)

    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "1234")},
            name="Test Device",
            manufacturer="Test Manufacturer",
            model="Test Model",
            suggested_area="Test Area",
        ),
        aliases=[er.COMPUTED_NAME, "my test light"],
    )
    for i in range(3):
        create_entity(
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                connections={("test", f"{i}abcd")},
                name="Test Service",
                manufacturer="Test Manufacturer",
                model="Test Model",
                suggested_area="Test Area",
                entry_type=dr.DeviceEntryType.SERVICE,
            )
        )
    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "5678")},
            name="Test Device 2",
            manufacturer="Test Manufacturer 2",
            model="Device 2",
            suggested_area="Test Area 2",
        )
    )
    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "9876")},
            name="Test Device 3",
            manufacturer="Test Manufacturer 3",
            model="Test Model 3A",
            suggested_area="Test Area 2",
        )
    )
    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "qwer")},
            name="Test Device 4",
            suggested_area="Test Area 2",
        )
    )
    device2 = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={("test", "9876-disabled")},
        name="Test Device 3 - disabled",
        manufacturer="Test Manufacturer 3",
        model="Test Model 3A",
        suggested_area="Test Area 2",
    )
    device_registry.async_update_device(
        device2.id, disabled_by=dr.DeviceEntryDisabler.USER
    )
    create_entity(device2, False)
    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "9876-no-name")},
            manufacturer="Test Manufacturer NoName",
            model="Test Model NoName",
            suggested_area="Test Area 2",
        )
    )
    create_entity(
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={("test", "9876-integer-values")},
            name="1",
            manufacturer="2",
            model="3",
            suggested_area="Test Area 2",
        )
    )
    exposed_entities_prompt = """Live Context: An overview of the areas and the devices in this smart home:
- names: '1'
  domain: light
  state: unavailable
  areas: Test Area 2
- names: Kitchen
  domain: light
  state: 'on'
  attributes:
    temperature: '0.9'
    humidity: '65'
- names: Living Room
  domain: light
  state: 'on'
  areas: Test Area, Alternative name
- names: Test Device, my test light
  domain: light
  state: unavailable
  areas: Test Area, Alternative name
- names: Test Device 2
  domain: light
  state: unavailable
  areas: Test Area 2
- names: Test Device 3
  domain: light
  state: unavailable
  areas: Test Area 2
- names: Test Device 4
  domain: light
  state: unavailable
  areas: Test Area 2
- names: Test Service
  domain: light
  state: unavailable
  areas: Test Area, Alternative name
- names: Test Service
  domain: light
  state: unavailable
  areas: Test Area, Alternative name
- names: Test Service
  domain: light
  state: unavailable
  areas: Test Area, Alternative name
- names: Unnamed Device
  domain: light
  state: unavailable
  areas: Test Area 2
"""
    stateless_exposed_entities_prompt = """Static Context: An overview of the areas and the devices in this smart home:
- names: '1'
  domain: light
  areas: Test Area 2
- names: Kitchen
  domain: light
- names: Living Room
  domain: light
  areas: Test Area, Alternative name
- names: Test Device, my test light
  domain: light
  areas: Test Area, Alternative name
- names: Test Device 2
  domain: light
  areas: Test Area 2
- names: Test Device 3
  domain: light
  areas: Test Area 2
- names: Test Device 4
  domain: light
  areas: Test Area 2
- names: Test Service
  domain: light
  areas: Test Area, Alternative name
- names: Test Service
  domain: light
  areas: Test Area, Alternative name
- names: Test Service
  domain: light
  areas: Test Area, Alternative name
- names: Unnamed Device
  domain: light
  areas: Test Area 2
"""
    first_part_prompt = (
        "When controlling Home Assistant always call the intent tools. "
        "Use HassTurnOn to lock and HassTurnOff to unlock a lock. "
        "When controlling a device, prefer passing just name and domain. "
        "When controlling an area, prefer passing just area name and domain."
    )
    no_timer_prompt = "This device is not able to start timers."

    area_prompt = (
        "When a user asks to turn on all devices of a specific type, "
        "ask user to specify an area, unless there is only one device of that type."
    )
    dynamic_context_prompt = """You ARE equipped to answer questions about the current state of
the home using the `GetLiveContext` tool. This is a primary function. Do not state you lack the
functionality if the question requires live data.
If the user asks about device existence/type (e.g., "Do I have lights in the bedroom?"): Answer
from the static context below.
If the user asks about the CURRENT state, value, or mode (e.g., "Is the lock locked?",
"Is the fan on?", "What mode is the thermostat in?", "What is the temperature outside?"):
    1.  Recognize this requires live data.
    2.  You MUST call `GetLiveContext`. This tool will provide the needed real-time information (like temperature from the local weather, lock status, etc.).
    3.  Use the tool's response** to answer the user accurately (e.g., "The temperature outside is [value from tool].").
For general knowledge questions not about the home: Answer truthfully from internal knowledge.
"""
    api = await llm.async_get_api(hass, "assist", llm_context)
    assert api.api_prompt == (
        f"""{first_part_prompt}
{area_prompt}
{no_timer_prompt}
{dynamic_context_prompt}
{stateless_exposed_entities_prompt}"""
    )

    # Verify that the GetLiveContext tool returns the same results as the exposed_entities_prompt
    result = await api.async_call_tool(
        llm.ToolInput(tool_name="GetLiveContext", tool_args={})
    )
    assert result == {
        "success": True,
        "result": exposed_entities_prompt,
    }

    # Fake that request is made from a specific device ID with an area
    llm_context.device_id = device.id
    area_prompt = (
        "You are in area Test Area and all generic commands like 'turn on the lights' "
        "should target this area."
    )
    api = await llm.async_get_api(hass, "assist", llm_context)
    assert api.api_prompt == (
        f"""{first_part_prompt}
{area_prompt}
{no_timer_prompt}
{dynamic_context_prompt}
{stateless_exposed_entities_prompt}"""
    )

    # Add floor
    floor = floor_registry.async_create("2")
    area_registry.async_update(area.id, floor_id=floor.floor_id)
    area_prompt = (
        "You are in area Test Area (floor 2) and all generic commands like 'turn on the lights' "
        "should target this area."
    )
    api = await llm.async_get_api(hass, "assist", llm_context)
    assert api.api_prompt == (
        f"""{first_part_prompt}
{area_prompt}
{no_timer_prompt}
{dynamic_context_prompt}
{stateless_exposed_entities_prompt}"""
    )

    # Register device for timers
    async_register_timer_handler(hass, device.id, lambda *args: None)

    api = await llm.async_get_api(hass, "assist", llm_context)
    # The no_timer_prompt is gone
    assert api.api_prompt == (
        f"""{first_part_prompt}
{area_prompt}
{dynamic_context_prompt}
{stateless_exposed_entities_prompt}"""
    )