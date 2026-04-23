def test_uscongress_bill_info(params, obb):
    """Test US Congress bill info."""
    params = {p: v for p, v in params.items() if v}

    result = obb.uscongress.bill_info(**params)
    assert result
    assert isinstance(result, OBBject)
    assert isinstance(result.results, CongressBillInfoData)
    assert isinstance(result.results.markdown_content, str)
    assert isinstance(result.results.raw_data, dict)