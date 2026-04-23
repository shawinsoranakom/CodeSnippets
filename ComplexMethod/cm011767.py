def _generate_value_for_type(
        random_sample: bool, field_name: str, type_hint: type[Any], default: Any
    ) -> Any:
        """
        Generates a value of a type based on the setting.
        """
        # look for name in type overrides
        if field_name in TYPE_OVERRIDES:
            return random.choice(TYPE_OVERRIDES[field_name])

        if type_hint is bool:
            return random.choice([True, False]) if random_sample else not default
        elif type_hint is int:
            # NOTE initially tried to use negation of the value, but it doesn't work because most types are ints
            # when they should be natural numbers + zero. Python types to cover these values aren't super convenient.
            return random.randint(0, 1000)
        elif type_hint is float:
            return random.uniform(0, 1000)
        elif type_hint is str:
            characters = string.ascii_letters + string.digits + string.punctuation
            return "".join(
                random.choice(characters) for _ in range(random.randint(1, 20))
            )
        elif is_type(type_hint, list):
            elem_type = getattr(
                type_hint,
                "__args__",
                [type(default[0])] if default and len(default) else [type(None)],
            )[0]
            new_default = default[0] if default and len(default) > 0 else None
            return [
                SamplingMethod._generate_value_for_type(
                    random_sample, field_name, elem_type, new_default
                )
                for _ in range(random.randint(1, 3))
            ]
        elif is_type(type_hint, set):  # noqa: set_linter
            indexable = list(default)
            elem_type = getattr(
                type_hint,
                "__args__",
                [type(indexable[0])] if default and len(default) else [type(None)],
            )[0]
            new_default = indexable[0] if default and len(default) > 0 else None
            return {  # noqa: set_linter
                SamplingMethod._generate_value_for_type(
                    random_sample, field_name, elem_type, new_default
                )
                for _ in range(random.randint(1, 3))
            }
        elif is_type(type_hint, OrderedSet):
            indexable = list(default)
            elem_type = getattr(
                type_hint,
                "__args__",
                [type(indexable[0])] if default and len(default) else [type(None)],
            )[0]
            new_default = indexable[0] if default and len(default) > 0 else None
            return OrderedSet(
                [
                    SamplingMethod._generate_value_for_type(
                        random_sample, field_name, elem_type, new_default
                    )
                    for _ in range(random.randint(1, 3))
                ]
            )
        elif is_type(type_hint, dict):
            key_type, value_type = getattr(
                type_hint,
                "__args__",
                map(type, next(iter(default.items())))
                if (default is not None and len(default))
                else (type(None), type(None)),
            )
            if default is not None and len(default.items()) > 0:
                default_key, default_val = next(iter(default.items()))
            else:
                default_key, default_val = None, None
            return {
                SamplingMethod._generate_value_for_type(
                    random_sample, field_name, key_type, default_key
                ): SamplingMethod._generate_value_for_type(
                    random_sample, field_name, value_type, default_val
                )
                for _ in range(random.randint(0, 3))
            }
        elif is_type(type_hint, Union) or is_type(type_hint, types.UnionType):
            # do whatever is not the type of default
            try:
                assert len(type_hint.__args__) > 1
            except AttributeError as err:
                raise ValueError("Union type with no args") from err
            if random_sample:
                new_type = random.choice(type_hint.__args__)
            else:
                new_type = random.choice(
                    [t for t in type_hint.__args__ if t is not type(default)]
                )
            try:
                new_default = new_type()
            except Exception:
                # if default constructor doesn't work, try None
                new_default = None

            return SamplingMethod._generate_value_for_type(
                random_sample, field_name, new_type, new_default
            )
        elif is_type(type_hint, tuple):
            args = getattr(
                type_hint,
                "__args__",
                tuple(map(type, default)),
            )
            zipped = zip(args, default)
            return tuple(
                map(  # noqa: C417
                    lambda x: SamplingMethod._generate_value_for_type(
                        random_sample, field_name, x[0], x[1]
                    ),
                    zipped,
                )
            )
        elif is_type(type_hint, Literal):
            try:
                if random_sample:
                    return random.choice(type_hint.__args__)
                else:
                    choices = [t for t in type_hint.__args__ if t != default]
                    if choices:
                        return random.choice(choices)
                    else:
                        return default
            except AttributeError as err:
                raise ValueError("Literal type with no args") from err
        elif is_optional_type(type_hint):
            try:
                elem_type = type_hint.__args__[0]
            except AttributeError as err:
                raise ValueError("Optional type with no args") from err
            if random_sample:
                return random.choice(
                    [
                        None,
                        SamplingMethod._generate_value_for_type(
                            random_sample, field_name, elem_type, default
                        ),
                    ]
                )
            else:
                if default is None:
                    return SamplingMethod._generate_value_for_type(
                        random_sample, field_name, elem_type, None
                    )
                else:
                    return None
        elif type_hint is type(None):
            return None
        elif is_callable_type(type_hint):
            try:
                return_type = list(type_hint.__args__)[-1]
            except AttributeError as err:
                raise ValueError("Callable type with no args") from err

            @wraps(lambda *args, **kwargs: None)
            def dummy_function(*args, **kwargs):  # type: ignore[no-untyped-def]
                return SamplingMethod._generate_value_for_type(
                    random_sample, field_name, return_type, None
                )

            return dummy_function
        elif type_hint == torch._ops.OpOverload:
            return torch.ops.aten.add.default
        elif TypeExemplars.contains(type_hint):
            return TypeExemplars.example(type_hint)
        elif type_hint == Any:
            return 1 if default != 1 else 2
        else:
            raise ValueError(f"Unable to process type {type_hint}. PRs welcome :)")