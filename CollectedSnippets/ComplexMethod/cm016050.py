def _flatten(
    key_prefix: Label, sub_schema: Definition, result: FlatIntermediateDefinition
) -> None:
    for k, value in sub_schema.items():
        if isinstance(k, tuple):
            if not all(isinstance(ki, str) for ki in k):
                raise AssertionError(
                    f"expected all elements of key tuple to be str, got {k}"
                )
            key_suffix: Label = k
        elif k is None:
            key_suffix = ()
        else:
            if not isinstance(k, str):
                raise AssertionError(f"expected key to be str, got {type(k)}")
            key_suffix = (k,)

        key: Label = key_prefix + key_suffix
        if isinstance(value, (TimerArgs, GroupedBenchmark)):
            if key in result:
                raise AssertionError(f"duplicate key: {key}")
            result[key] = value
        else:
            if not isinstance(value, dict):
                raise AssertionError(f"expected value to be dict, got {type(value)}")
            _flatten(key_prefix=key, sub_schema=value, result=result)