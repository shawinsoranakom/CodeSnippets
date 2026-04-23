async def test_setup_provide_implementation(hass: HomeAssistant) -> None:
    """Test that we provide implementations."""
    legacy_entry = MockConfigEntry(
        domain="legacy",
        version=1,
        data={"auth_implementation": "cloud"},
    )
    none_cloud_entry = MockConfigEntry(
        domain="no_cloud",
        version=1,
        data={"auth_implementation": "somethingelse"},
    )
    none_cloud_entry.add_to_hass(hass)
    legacy_entry.add_to_hass(hass)
    account_link.async_setup(hass)

    with (
        patch(
            "homeassistant.components.cloud.account_link._get_services",
            return_value=[
                {"service": "test", "min_version": "0.1.0"},
                {"service": "too_new", "min_version": "1000000.0.0"},
                {"service": "dev", "min_version": "2022.9.0"},
                {
                    "service": "deprecated",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
                {
                    "service": "legacy",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
                {
                    "service": "no_cloud",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
            ],
        ),
        patch(
            "homeassistant.components.cloud.account_link.HA_VERSION",
            "2022.9.0.dev20220817",
        ),
    ):
        assert (
            await config_entry_oauth2_flow.async_get_implementations(
                hass, "non_existing"
            )
            == {}
        )
        assert (
            await config_entry_oauth2_flow.async_get_implementations(hass, "too_new")
            == {}
        )
        assert (
            await config_entry_oauth2_flow.async_get_implementations(hass, "deprecated")
            == {}
        )
        assert (
            await config_entry_oauth2_flow.async_get_implementations(hass, "no_cloud")
            == {}
        )

        implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "test"
        )

        legacy_implementations = (
            await config_entry_oauth2_flow.async_get_implementations(hass, "legacy")
        )

        dev_implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "dev"
        )

    assert "cloud" in implementations
    assert implementations["cloud"].domain == "cloud"
    assert implementations["cloud"].service == "test"
    assert implementations["cloud"].hass is hass

    assert "cloud" in legacy_implementations
    assert legacy_implementations["cloud"].domain == "cloud"
    assert legacy_implementations["cloud"].service == "legacy"
    assert legacy_implementations["cloud"].hass is hass

    assert "cloud" in dev_implementations
    assert dev_implementations["cloud"].domain == "cloud"
    assert dev_implementations["cloud"].service == "dev"
    assert dev_implementations["cloud"].hass is hass