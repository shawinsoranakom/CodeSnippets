def _check_sparse_embedding(data, check_tokens=False):
    expected_weights = [
        {"token_id": 32, "weight": 0.0552978515625, "token": "?"},
        {"token_id": 70, "weight": 0.09808349609375, "token": "the"},
        {"token_id": 83, "weight": 0.08154296875, "token": "is"},
        {"token_id": 111, "weight": 0.11810302734375, "token": "of"},
        {"token_id": 4865, "weight": 0.1171875, "token": "What"},
        {"token_id": 9942, "weight": 0.292236328125, "token": "France"},
        {"token_id": 10323, "weight": 0.2802734375, "token": "capital"},
    ]
    expected_embed = {x["token_id"]: x for x in expected_weights}

    assert len(data) == len(expected_embed)
    for entry in data:
        expected_val = expected_embed[_get_attr_or_val(entry, "token_id")]
        assert _float_close(
            expected_val["weight"], _get_attr_or_val(entry, "weight")
        ), f"actual embed {entry} not equal to {expected_val}"
        if check_tokens:
            assert expected_val["token"] == _get_attr_or_val(entry, "token"), (
                f"actual embed {entry} not equal to {expected_val}"
            )
        else:
            assert _get_attr_or_val(entry, "token") is None, (
                f"{entry} should not return token"
            )