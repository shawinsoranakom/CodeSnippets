async def test_update_with_xml_convert_json_attrs_with_jsonattr_template(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test attributes get extracted from a JSON result that was converted from XML."""

    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        headers={"content-type": "text/xml"},
        text='<?xml version="1.0" encoding="utf-8"?><response><scan>0</scan><ver>12556</ver><count>48</count><ssid>alexander</ssid><bss><valid>0</valid><name>0</name><privacy>0</privacy><wlan>123</wlan><strength>0</strength></bss><led0>0</led0><led1>0</led1><led2>0</led2><led3>0</led3><led4>0</led4><led5>0</led5><led6>0</led6><led7>0</led7><btn0>up</btn0><btn1>up</btn1><btn2>up</btn2><btn3>up</btn3><pot0>0</pot0><usr0>0</usr0><temp0>0x0XF0x0XF</temp0><time0> 0</time0></response>',
    )
    assert await async_setup_component(
        hass,
        SENSOR_DOMAIN,
        {
            SENSOR_DOMAIN: {
                "platform": DOMAIN,
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.response.bss.wlan }}",
                "json_attributes_path": "$.response",
                "json_attributes": ["led0", "led1", "temp0", "time0", "ver"],
                "name": "foo",
                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                "verify_ssl": "true",
                "timeout": 30,
            }
        },
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all(SENSOR_DOMAIN)) == 1
    state = hass.states.get("sensor.foo")

    assert state.state == "123"
    assert state.attributes["led0"] == "0"
    assert state.attributes["led1"] == "0"
    assert state.attributes["temp0"] == "0x0XF0x0XF"
    assert state.attributes["time0"] == "0"
    assert state.attributes["ver"] == "12556"