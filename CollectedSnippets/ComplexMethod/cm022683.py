def test_density_to_air_quality() -> None:
    """Test map PM2.5 density to HomeKit AirQuality level."""
    assert density_to_air_quality(0) == 1
    assert density_to_air_quality(9) == 1
    assert density_to_air_quality(9.1) == 2
    assert density_to_air_quality(12) == 2
    assert density_to_air_quality(35.4) == 2
    assert density_to_air_quality(35.5) == 3
    assert density_to_air_quality(55.4) == 3
    assert density_to_air_quality(55.5) == 4
    assert density_to_air_quality(125.4) == 4
    assert density_to_air_quality(125.5) == 5
    assert density_to_air_quality(200) == 5