def test_aliases(arg_spec, parameters, expected, deprecation, warning):
    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.validated_parameters == expected
    assert result.error_messages == []
    assert result._aliases == {
        alias: param
        for param, value in arg_spec.items()
        for alias in value.get("aliases", [])
    }

    if deprecation:
        assert deprecation == result._deprecations[0]
    else:
        assert result._deprecations == []

    if warning:
        assert warning == result._warnings[0]
    else:
        assert result._warnings == []