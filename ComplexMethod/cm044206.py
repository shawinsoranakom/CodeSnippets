def test_charting_equity_historical_market_cap(params, headers):
    """Test chart equity historical market cap."""
    params = {p: v for p, v in params.items() if v}
    body = (json.dumps({"extra_params": {"chart_params": {"title": "test chart"}}}),)
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/equity/historical_market_cap?{query_str}"
    result = requests.get(url, headers=headers, timeout=10, json=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]