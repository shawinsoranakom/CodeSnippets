def test_charting_econometrics_correlation_matrix(params, headers):
    """Test chart econometrics correlation matrix."""
    # pylint:disable=import-outside-toplevel
    from pandas import DataFrame

    url = "http://0.0.0.0:8000/api/v1/equity/price/historical?symbol=AAPL,MSFT,GOOG&provider=yfinance"
    result = requests.get(url, headers=headers, timeout=10)
    df = DataFrame(result.json()["results"])
    df = df.pivot(index="date", columns="symbol", values="close").reset_index()
    body = df.to_dict(orient="records")

    params = {p: v for p, v in params.items() if v}

    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/econometrics/correlation_matrix?{query_str}"
    result = requests.post(url, headers=headers, timeout=10, data=json.dumps(body))

    assert isinstance(result, requests.Response)
    assert result.status_code == 200

    chart = result.json()["chart"]
    fig = chart.pop("fig", {})

    assert chart
    assert not fig
    assert list(chart.keys()) == ["content", "format"]