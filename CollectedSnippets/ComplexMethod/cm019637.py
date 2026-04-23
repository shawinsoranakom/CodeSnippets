async def test_create_todo_list_item(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_picnic_api: MagicMock
) -> None:
    """Test for creating a picnic cart item."""
    assert len(mock_picnic_api.get_cart.mock_calls) == 1

    mock_picnic_api.search = Mock()
    mock_picnic_api.search.return_value = [
        {
            "items": [
                {
                    "id": 321,
                    "name": "Picnic Melk",
                    "unit_quantity": "2 liter",
                }
            ]
        }
    ]

    mock_picnic_api.add_product = Mock()

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "Melk"},
        target={ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    args = mock_picnic_api.search.call_args
    assert args
    assert args[0][0] == "Melk"

    args = mock_picnic_api.add_product.call_args
    assert args
    assert args[0][0] == "321"
    assert args[0][1] == 1

    assert len(mock_picnic_api.get_cart.mock_calls) == 2