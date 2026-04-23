def test_charting_technical_zlma(params, headers):
    """Test chart ta zlma."""
    params = {p: v for p, v in params.items() if v}
    body = json.dumps(get_equity_data())

    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/technical/zlma?{query_str}"
    result = requests.post(url, headers=headers, timeout=10, data=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]