def test_charting_economy_shipping_chokepoint_info(params, headers):
    """Test chart economy shipping chokepoint info."""
    params = {p: v for p, v in params.items() if v}
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/economy/shipping/chokepoint_info?{query_str}"
    result = requests.get(url, headers=headers, timeout=10)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]