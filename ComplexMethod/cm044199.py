def test_charting_technical_relative_rotation(params):
    """Test charting technical relative rotation endpoint."""
    params = {p: v for p, v in params.items() if v}
    data_params = dict(
        symbol="AAPL,MSFT,GOOGL,AMZN,SPY",
        provider="yfinance",
        start_date="2022-01-01",
        end_date="2024-01-01",
    )
    data_query_str = get_querystring(data_params, [])
    data_url = f"http://0.0.0.0:8000/api/v1/equity/price/historical?{data_query_str}"
    data_result = requests.get(data_url, headers=get_headers(), timeout=10).json()[
        "results"
    ]
    body = json.dumps({"data": data_result})
    query_str = get_querystring(params, ["data"])
    url = f"http://0.0.0.0:8000/api/v1/technical/relative_rotation?{query_str}"
    result = requests.post(url, headers=get_headers(), timeout=10, data=body)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200
    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]