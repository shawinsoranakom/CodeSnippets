def test_derivatives_options_chains(params, obb):
    """Test the options chains endpoint."""
    result = obb.derivatives.options.chains(**params)
    assert result
    assert isinstance(result, OBBject)
    result = result.results  # type: ignore
    list_msg = "Unexpected data format, expected List"
    oi_msg = "Unexpected keys in total_oi property, expected ['total', 'expiration', 'strike']"
    assert isinstance(result.expirations, list), list_msg  # type: ignore
    assert isinstance(result.strikes, list), list_msg  # type: ignore
    assert isinstance(result.contract_symbol, list), list_msg  # type: ignore
    assert hasattr(result, "total_oi"), "Missing total_oi property"  # type: ignore
    assert isinstance(result.total_oi, dict), "Unexpected property format, expected dictionary."  # type: ignore
    assert list(result.total_oi) == ["total", "expiration", "strike"], oi_msg  # type: ignore
    assert hasattr(result, "dataframe"), "Missing dataframe attribute"  # type: ignore
    assert result.has_iv, "Expected implied volatility data"  # type: ignore
    assert len(getattr(result, "dataframe", [])) == len(result.contract_symbol)