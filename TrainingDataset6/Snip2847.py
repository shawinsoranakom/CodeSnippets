def test_decimal_encoder_infinity():
    data = {"value": Decimal("Infinity")}
    assert isinf(jsonable_encoder(data)["value"])
    data = {"value": Decimal("-Infinity")}
    assert isinf(jsonable_encoder(data)["value"])