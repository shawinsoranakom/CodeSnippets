async def test_register_multiple_controllers(hass: HomeAssistant) -> None:
    """Test register multiple controllers.

    Each registered controller must get its own key/certificate pair,
    which must not get overwritten when a new controller is added.
    """

    controller_1 = {
        "hostname": "shc111111",
        "mac": "test-mac1",
        "host": "1.1.1.1",
        "register": {
            "token": "abc:shc111111",
            "cert": b"content_cert1",
            "key": b"content_key1",
        },
    }
    controller_2 = {
        "hostname": "shc222222",
        "mac": "test-mac2",
        "host": "2.2.2.2",
        "register": {
            "token": "abc:shc222222",
            "cert": b"content_cert2",
            "key": b"content_key2",
        },
    }

    # Set up controller 1
    ctrl_1_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "boschshcpy.session.SHCSession.mdns_info",
            return_value=SHCInformation,
        ),
        patch(
            "boschshcpy.information.SHCInformation.name",
            new_callable=PropertyMock,
            return_value=controller_1["hostname"],
        ),
        patch(
            "boschshcpy.information.SHCInformation.unique_id",
            new_callable=PropertyMock,
            return_value=controller_1["mac"],
        ),
    ):
        ctrl_1_result2 = await hass.config_entries.flow.async_configure(
            ctrl_1_result["flow_id"],
            {"host": controller_1["host"]},
        )

    with (
        patch(
            "boschshcpy.register_client.SHCRegisterClient.register",
            return_value=controller_1["register"],
        ),
        patch("os.mkdir"),
        patch("homeassistant.components.bosch_shc.config_flow.open"),
        patch("boschshcpy.session.SHCSession.authenticate"),
        patch(
            "homeassistant.components.bosch_shc.async_setup_entry",
            return_value=True,
        ),
    ):
        ctrl_1_result3 = await hass.config_entries.flow.async_configure(
            ctrl_1_result2["flow_id"],
            {"password": "test"},
        )
        await hass.async_block_till_done()

    assert ctrl_1_result3["type"] is FlowResultType.CREATE_ENTRY
    assert ctrl_1_result3["title"] == "shc111111"
    assert ctrl_1_result3["context"]["unique_id"] == controller_1["mac"]
    assert ctrl_1_result3["data"] == {
        "host": "1.1.1.1",
        "ssl_certificate": hass.config.path(DOMAIN, controller_1["mac"], CONF_SHC_CERT),
        "ssl_key": hass.config.path(DOMAIN, controller_1["mac"], CONF_SHC_KEY),
        "token": "abc:shc111111",
        "hostname": "shc111111",
    }

    # Set up controller 2
    ctrl_2_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "boschshcpy.session.SHCSession.mdns_info",
            return_value=SHCInformation,
        ),
        patch(
            "boschshcpy.information.SHCInformation.name",
            new_callable=PropertyMock,
            return_value=controller_2["hostname"],
        ),
        patch(
            "boschshcpy.information.SHCInformation.unique_id",
            new_callable=PropertyMock,
            return_value=controller_2["mac"],
        ),
    ):
        ctrl_2_result2 = await hass.config_entries.flow.async_configure(
            ctrl_2_result["flow_id"],
            {"host": controller_2["host"]},
        )

    with (
        patch(
            "boschshcpy.register_client.SHCRegisterClient.register",
            return_value=controller_2["register"],
        ),
        patch("os.mkdir"),
        patch("homeassistant.components.bosch_shc.config_flow.open"),
        patch("boschshcpy.session.SHCSession.authenticate"),
        patch(
            "homeassistant.components.bosch_shc.async_setup_entry",
            return_value=True,
        ),
    ):
        ctrl_2_result3 = await hass.config_entries.flow.async_configure(
            ctrl_2_result2["flow_id"],
            {"password": "test"},
        )
        await hass.async_block_till_done()

    assert ctrl_2_result3["type"] is FlowResultType.CREATE_ENTRY
    assert ctrl_2_result3["title"] == "shc222222"
    assert ctrl_2_result3["context"]["unique_id"] == controller_2["mac"]
    assert ctrl_2_result3["data"] == {
        "host": "2.2.2.2",
        "ssl_certificate": hass.config.path(DOMAIN, controller_2["mac"], CONF_SHC_CERT),
        "ssl_key": hass.config.path(DOMAIN, controller_2["mac"], CONF_SHC_KEY),
        "token": "abc:shc222222",
        "hostname": "shc222222",
    }

    # Check that each controller has its own key/certificate pair
    assert (
        ctrl_1_result3["data"]["ssl_certificate"]
        != ctrl_2_result3["data"]["ssl_certificate"]
    )
    assert ctrl_1_result3["data"]["ssl_key"] != ctrl_2_result3["data"]["ssl_key"]