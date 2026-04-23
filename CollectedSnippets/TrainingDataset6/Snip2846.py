def test_decimal_encoder_nan():
    data = {"value": Decimal("NaN")}
    assert isnan(jsonable_encoder(data)["value"])