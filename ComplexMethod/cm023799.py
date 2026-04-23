def test_nx584_zone_sensor_bypassed() -> None:
    """Test for the NX584 zone sensor."""
    zone = {"number": 1, "name": "foo", "state": True, "bypassed": True}
    sensor = nx584.NX584ZoneSensor(zone, "motion")
    assert sensor.name == "foo"
    assert not sensor.should_poll
    assert sensor.is_on
    assert sensor.extra_state_attributes["zone_number"] == 1
    assert sensor.extra_state_attributes["bypassed"]

    zone["state"] = False
    zone["bypassed"] = False
    assert not sensor.is_on
    assert not sensor.extra_state_attributes["bypassed"]