def test_equity_discovery_filings(params, obb):
    """Test the equity discovery filings endpoint."""
    params = {p: v for p, v in params.items() if v}

    result = obb.equity.discovery.filings(**params)
    assert result
    assert isinstance(result, OBBject)
    if isinstance(result.results, list):
        assert len(result.results) > 0
    else:
        assert result.results is not None