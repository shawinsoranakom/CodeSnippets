def _compute_kwargs(cls: ConfigType) -> dict[str, dict[str, Any]]:
    # Save time only getting attr docs if we're generating help text
    cls_docs = get_attr_docs(cls) if NEEDS_HELP else {}
    kwargs = {}
    for field in fields(cls):
        # Get the set of possible types for the field
        type_hints: set[TypeHint] = get_type_hints(field.type)

        # If the field is a dataclass, we can use the model_validate_json
        generator = (th for th in type_hints if is_dataclass(th))
        dataclass_cls = next(generator, None)

        # Get the default value of the field
        if field.default is not MISSING:
            default = field.default
            # Handle pydantic.Field defaults
            if isinstance(default, FieldInfo):
                if default.default_factory is None:
                    default = default.default
                else:
                    # VllmConfig's Fields have default_factory set to config classes.
                    # These could emit logs on init, which would be confusing.
                    with suppress_logging():
                        default = default.default_factory()  # type: ignore[call-arg]
        elif field.default_factory is not MISSING:
            default = field.default_factory()

        # Get the help text for the field
        name = field.name
        help = cls_docs.get(name, "").strip()
        # Escape % for argparse
        help = help.replace("%", "%%")

        # Initialise the kwargs dictionary for the field
        kwargs[name] = {"default": default, "help": help}

        # Set other kwargs based on the type hints
        json_tip = (
            "Should either be a valid JSON string or JSON keys passed individually."
        )
        if dataclass_cls is not None:

            def parse_dataclass(val: str, cls=dataclass_cls) -> Any:
                try:
                    return TypeAdapter(cls).validate_json(val)
                except ValidationError as e:
                    raise argparse.ArgumentTypeError(repr(e)) from e

            kwargs[name]["type"] = parse_dataclass
            kwargs[name]["help"] += _maybe_add_docs_url(dataclass_cls)
            kwargs[name]["help"] += f"\n\n{json_tip}"
        elif contains_type(type_hints, bool):
            # Creates --no-<name> and --<name> flags
            kwargs[name]["action"] = argparse.BooleanOptionalAction
        elif contains_type(type_hints, Literal):
            kwargs[name].update(literal_to_kwargs(type_hints))
        elif contains_type(type_hints, tuple):
            kwargs[name].update(collection_to_kwargs(type_hints, tuple))
        elif contains_type(type_hints, list):
            kwargs[name].update(collection_to_kwargs(type_hints, list))
        elif contains_type(type_hints, set):
            kwargs[name].update(collection_to_kwargs(type_hints, set))
        elif contains_type(type_hints, int):
            if name == "max_model_len":
                kwargs[name]["type"] = human_readable_int_or_auto
                kwargs[name]["help"] += f"\n\n{human_readable_int_or_auto.__doc__}"
            elif name in ("max_num_batched_tokens", "kv_cache_memory_bytes"):
                kwargs[name]["type"] = human_readable_int
                kwargs[name]["help"] += f"\n\n{human_readable_int.__doc__}"
            else:
                kwargs[name]["type"] = int
        elif contains_type(type_hints, float):
            kwargs[name]["type"] = float
        elif contains_type(type_hints, dict) and (
            contains_type(type_hints, str)
            or any(is_not_builtin(th) for th in type_hints)
        ):
            kwargs[name]["type"] = union_dict_and_str
        elif contains_type(type_hints, dict):
            kwargs[name]["type"] = parse_type(json.loads)
            kwargs[name]["help"] += f"\n\n{json_tip}"
        elif contains_type(type_hints, str) or any(
            is_not_builtin(th) for th in type_hints
        ):
            kwargs[name]["type"] = str
        else:
            raise ValueError(f"Unsupported type {type_hints} for argument {name}.")

        # If the type hint was a sequence of literals, use the helper function
        # to update the type and choices
        if get_origin(kwargs[name].get("type")) is Literal:
            kwargs[name].update(literal_to_kwargs({kwargs[name]["type"]}))

        # If None is in type_hints, make the argument optional.
        # But not if it's a bool, argparse will handle this better.
        if type(None) in type_hints and not contains_type(type_hints, bool):
            kwargs[name]["type"] = optional_type(kwargs[name]["type"])
            if kwargs[name].get("choices"):
                kwargs[name]["choices"].append("None")
    return kwargs