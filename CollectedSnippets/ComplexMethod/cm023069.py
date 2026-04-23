async def test_select(hass: HomeAssistant) -> None:
    """Test getting data from the mocked select entity."""
    select = MockSelectEntity()
    assert select.current_option == "option_one"
    assert select.state == "option_one"
    assert select.options == ["option_one", "option_two", "option_three"]

    # Test none selected
    select._attr_current_option = None
    assert select.current_option is None
    assert select.state is None

    # Test none existing selected
    select._attr_current_option = "option_four"
    assert select.current_option == "option_four"
    assert select.state is None

    select.hass = hass

    with pytest.raises(NotImplementedError):
        await select.async_first()

    with pytest.raises(NotImplementedError):
        await select.async_last()

    with pytest.raises(NotImplementedError):
        await select.async_next(cycle=False)

    with pytest.raises(NotImplementedError):
        await select.async_previous(cycle=False)

    with pytest.raises(NotImplementedError):
        await select.async_select_option("option_one")

    select.select_option = MagicMock()
    select._attr_current_option = None

    await select.async_first()
    assert select.select_option.call_args[0][0] == "option_one"

    await select.async_last()
    assert select.select_option.call_args[0][0] == "option_three"

    await select.async_next(cycle=False)
    assert select.select_option.call_args[0][0] == "option_one"

    await select.async_previous(cycle=False)
    assert select.select_option.call_args[0][0] == "option_three"

    await select.async_select_option("option_two")
    assert select.select_option.call_args[0][0] == "option_two"

    assert select.select_option.call_count == 5

    assert select.capability_attributes[ATTR_OPTIONS] == [
        "option_one",
        "option_two",
        "option_three",
    ]