def test_charting_technical_cones(params, obb):
    """Test chart ta cones."""
    params = {p: v for p, v in params.items() if v}

    params["data"] = get_equity_data()

    result = obb.technical.cones(**params)
    assert result
    assert isinstance(result, OBBject)
    assert len(result.results) > 0
    assert result.chart.content
    assert isinstance(result.chart.fig, OpenBBFigure)