def _dict_to_dataclass(cls, data):
    cls = _resolve_schema_cls(cls)
    if isinstance(cls, str):
        raise AssertionError(f"Unresolved class type: '{cls}'.")
    if typing.get_origin(cls) is Annotated:
        return _dict_to_dataclass(cls.__origin__, data)
    if typing.get_origin(cls) in (typing.Union, types.UnionType) and type(
        None
    ) in typing.get_args(cls):
        if data is None:
            return None
        ty_args = typing.get_args(cls)
        if len(ty_args) != 2:
            raise AssertionError(f"expected 2 type args, got {len(ty_args)}")
        return _dict_to_dataclass(ty_args[0], data)
    elif isinstance(cls, type) and issubclass(cls, _Union):
        if not isinstance(data, dict):
            raise AssertionError(f"expected dict, got {type(data).__name__}")
        if len(data) != 1:
            raise AssertionError(f"expected dict with 1 key, got {len(data)}")
        _type = next(iter(data.keys()))
        _value = next(iter(data.values()))
        if not isinstance(_type, str):
            raise AssertionError(f"expected str key, got {type(_type).__name__}")
        type_hints = typing.get_type_hints(cls, globalns=vars(schema))
        field_type = type_hints[_type]
        # pyrefly: ignore [missing-attribute]
        return cls.create(**{_type: _dict_to_dataclass(field_type, _value)})
    elif dataclasses.is_dataclass(cls):
        fields = {}
        type_hints = typing.get_type_hints(cls, globalns=vars(schema))
        # For forward compatibility consideration, we ignore all the keys
        # that are not showing up in the dataclass definition.
        for f in dataclasses.fields(cls):
            name = f.name
            if name not in data:
                continue
            new_field_obj = _dict_to_dataclass(type_hints[name], data[name])
            fields[name] = new_field_obj
        return cls(**fields)  # type: ignore[operator]
    elif isinstance(data, list):
        if len(data) == 0:
            return data
        d_type = typing.get_args(cls)[0]
        return [_dict_to_dataclass(d_type, d) for d in data]
    elif isinstance(data, dict):
        v_type = typing.get_args(cls)[1]
        return {k: _dict_to_dataclass(v_type, v) for k, v in data.items()}
    elif cls is float:
        return float(data)
    return data