def test_charting_derivatives_options_surface(params, headers):
    """Test chart derivatives options surface."""
    # pylint:disable=import-outside-toplevel
    params = {p: v for p, v in params.items() if v and p != "data"}

    data_url = "http://0.0.0.0:8000/api/v1/derivatives/options/chains?symbol=AAPL&provider=cboe"
    data_result = requests.get(data_url, headers=headers, timeout=10).json()
    data = data_result.get("results", [])
    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/derivatives/options/surface?{query_str}"
    result = requests.post(
        url, headers=headers, timeout=10, data=json.dumps({"data": data})
    )
    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]