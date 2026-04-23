def test_charting_etf_price_performance(params, headers):
    """Test chart equity price performance."""
    params = {p: v for p, v in params.items() if v}
    body = (json.dumps({"extra_params": {"chart_params": {"orientation": "v"}}}),)
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/etf/price_performance?{query_str}"
    result = requests.get(url, headers=headers, timeout=10, json=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]