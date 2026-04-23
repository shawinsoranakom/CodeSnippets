def test_charting_fixedincome_government_yield_curve(params, headers):
    """Test chart fixedincome government yield curve."""
    params = {p: v for p, v in params.items() if v}
    body = (json.dumps({"extra_params": {"chart_params": {"title": "test chart"}}}),)
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/fixedincome/government/yield_curve?{query_str}"
    result = requests.get(url, headers=headers, timeout=10, json=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]