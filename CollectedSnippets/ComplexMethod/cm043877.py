def test_get_dataflow_parameters_time_period_options(imf_metadata):
    dataflow_id = "CPI"
    parameters = imf_metadata.get_dataflow_parameters(dataflow_id)
    time_period_options = parameters.get("TIME_PERIOD")

    assert time_period_options is not None
    assert len(time_period_options) == 6
    assert any(option["value"] == "YYYY" for option in time_period_options)
    assert any(option["value"] == "YYYY-MM" for option in time_period_options)
    assert any(option["value"] == "YYYY-QQ" for option in time_period_options)
    assert any(option["value"] == "YYYY-SS" for option in time_period_options)
    assert any("Start Date:" in option["label"] for option in time_period_options)
    assert any("End Date:" in option["label"] for option in time_period_options)