def test_commodity_weather_bulletins_download(params, obb):
    """Test Commodity Weather Bulletins Download endpoint."""
    result = obb.commodity.weather_bulletins_download(**params)
    assert result
    assert isinstance(result, list)
    assert len(result) > 0
    for bulletin in result:
        assert isinstance(bulletin, dict)
        assert bulletin["content"]
        assert bulletin["data_format"]["data_type"] == "pdf"