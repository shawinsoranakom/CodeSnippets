def test_scale_arguments(input_data, expected_output):
    """Test the scale_arguments method."""
    kwargs = {
        "provider_choices": {},
        "standard_params": {},
        "extra_params": input_data,
    }
    m = Metadata(
        arguments=kwargs,
        route="test",
        timestamp=datetime.now(),
        duration=0,
    )
    arguments = m.arguments

    for arg in arguments:  # pylint: disable=E1133
        if "columns" in arguments[arg]:
            # compare the column names disregarding the order with the expected output
            assert sorted(arguments["extra_params"][arg]["columns"]) == sorted(
                expected_output[arg]["columns"]
            )
            assert arguments[arg]["type"] == expected_output[arg]["type"]
        else:
            # assert m.arguments["extra_params"] == expected_output
            keys = list(arguments["extra_params"].keys())
            expected_keys = list(expected_output.keys())
            assert sorted(keys) == sorted(expected_keys)

            for key in keys:
                if "type" in arguments["extra_params"][key]:
                    assert (
                        arguments["extra_params"][key]["type"]
                        == expected_output[key]["type"]
                    )
                    assert sorted(arguments["extra_params"][key]["columns"]) == sorted(
                        expected_output[key]["columns"]
                    )
                else:
                    assert arguments["extra_params"][key] == expected_output[key]