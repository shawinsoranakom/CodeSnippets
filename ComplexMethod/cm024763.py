async def test_option_updates(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test handling option updates."""

    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [GOOD_CURRENCY, GOOD_CURRENCY_2],
                CONF_EXCHANGE_RATES: [GOOD_EXCHANGE_RATE, GOOD_EXCHANGE_RATE_2],
            },
        )
        await hass.async_block_till_done()

        entities = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        assert len(entities) == 4
        currencies = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "wallet" in entity.unique_id
        ]

        rates = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "xe" in entity.unique_id
        ]

        assert currencies == [GOOD_CURRENCY, GOOD_CURRENCY_2]
        assert rates == [GOOD_EXCHANGE_RATE, GOOD_EXCHANGE_RATE_2]

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [GOOD_CURRENCY],
                CONF_EXCHANGE_RATES: [GOOD_EXCHANGE_RATE],
            },
        )
        await hass.async_block_till_done()

        entities = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        assert len(entities) == 2
        currencies = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "wallet" in entity.unique_id
        ]

        rates = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "xe" in entity.unique_id
        ]

        assert currencies == [GOOD_CURRENCY]
        assert rates == [GOOD_EXCHANGE_RATE]