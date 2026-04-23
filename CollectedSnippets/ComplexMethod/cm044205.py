def test_charting_derivatives_futures_curve(params, headers):
    """Test chart derivatives futures curve."""
    params = {p: v for p, v in params.items() if v}
    body = (json.dumps({"extra_params": {"chart_params": {"title": "test chart"}}}),)
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/derivatives/futures/curve?{query_str}"
    result = requests.get(url, headers=headers, timeout=30, json=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]