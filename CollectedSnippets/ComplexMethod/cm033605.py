def test_profile(test_case: _TestCase) -> None:
    output = test_case.parameters.get_test_output()

    if isinstance(output.payload, Exception):
        if type(output.payload) is not type(test_case.expected.payload):
            raise Exception('unexpected exception') from output.payload

        assert str(output.payload) == str(test_case.expected.payload)
    else:
        assert output.payload == test_case.expected.payload
        assert type(output.round_trip) is type(test_case.expected.round_trip)

        if isinstance(output.round_trip, AnsibleRuntimeError):
            assert str(output.round_trip._original_message) == str(test_case.expected.round_trip._original_message)
        else:
            assert output.round_trip == test_case.expected.round_trip

        assert not set(output.tags).symmetric_difference(test_case.expected.tags)