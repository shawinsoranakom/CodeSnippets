def from_dict(cls, data_dict: dict[str, T.Any]) -> T.Self:
        """Load the contents from a serialized python dict into this dataclass

        Parameters
        ----------
        data_dict
            The data to load into the dataclass
        """
        inbound = set(data_dict)
        all_fields = set(f.name for f in fields(cls))
        required = set(f.name for f in fields(cls)
                       if f.default is MISSING and f.default_factory is MISSING)
        if not inbound.issubset(all_fields):
            raise ValueError(f"Dictionary keys {sorted(inbound)} should be a subset of dataclass "
                             f"params {sorted(all_fields)}")
        if not required.issubset(inbound):
            raise ValueError(f"Dataclass params {sorted(required)} should be a subset of "
                             f"dictionary keys {sorted(inbound)}")
        type_hints = T.get_type_hints(cls)
        kwargs: dict[str, T.Any] = {}
        for f in fields(cls):
            if f.name not in data_dict:
                continue
            field_type = type_hints.get(f.name)
            val = data_dict[f.name]
            converted = cls._convert_dtype(field_type, val)
            if converted is not None:
                kwargs[f.name] = converted
                continue
            if isinstance(val, dict):
                kwargs[f.name] = cls._parse_dict(field_type, val)
                continue
            if isinstance(val, (list, tuple)):
                kwargs[f.name] = cls._parse_list(field_type, val)
                continue
            kwargs[f.name] = val
        return cls(**kwargs)