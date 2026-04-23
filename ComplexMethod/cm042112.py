def test_extract_time_comps(mock_dataset):
    time_comps = ["year", "month", "day", "hour", "dayofweek", "is_weekend"]
    etc = ExtractTimeComps(time_col="date1", time_comps=time_comps)
    transformed = etc.fit_transform(mock_dataset.copy())

    for comp in time_comps:
        assert comp in transformed.columns
    assert transformed["year"][0] == 2020
    assert transformed["month"][0] == 1
    assert transformed["day"][0] == 1
    assert transformed["hour"][0] == 0
    assert transformed["dayofweek"][0] == 3
    assert transformed["is_weekend"][0] == 0