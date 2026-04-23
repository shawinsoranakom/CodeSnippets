def test_charting_technical_sma(params, obb):
    """Test chart ta sma."""
    params = {p: v for p, v in params.items() if v}

    params["data"] = get_equity_data()

    result = obb.technical.sma(**params)
    assert result
    assert isinstance(result, OBBject)
    assert len(result.results) > 0
    assert result.chart.content
    assert isinstance(result.chart.fig, OpenBBFigure)