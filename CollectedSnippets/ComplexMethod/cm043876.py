def test_get_dataflow_parameters_cpi(imf_metadata):
    dataflow_id = "CPI"
    parameters = imf_metadata.get_dataflow_parameters(dataflow_id)

    assert "COUNTRY" in parameters
    assert "FREQUENCY" in parameters
    assert "TIME_PERIOD" in parameters
    assert isinstance(parameters["COUNTRY"], list)
    assert isinstance(parameters["FREQUENCY"], list)
    assert isinstance(parameters["TIME_PERIOD"], list)
    assert any(option["value"] == "USA" for option in parameters["COUNTRY"])
    assert any(option["value"] == "A" for option in parameters["FREQUENCY"])
    assert any(option["value"] == "YYYY" for option in parameters["TIME_PERIOD"])