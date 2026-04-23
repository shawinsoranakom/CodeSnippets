def test_standard_models(standard_model):
    """Test the standard models."""
    assert issubclass(standard_model, Data) or issubclass(
        standard_model, QueryParams
    ), f"{standard_model.__name__} should be a subclass of Data or QueryParams"

    fields = standard_model.model_fields

    for name, field in fields.items():
        assert isinstance(
            field, FieldInfo
        ), f"Field {name} should be a ModelField instance"
        if "QueryParams" in standard_model.__name__:
            if name in QUERY_DESCRIPTIONS:
                assert QUERY_DESCRIPTIONS[name] in getattr(field, "description"), (
                    f"Description for {name} is incorrect for the {standard_model.__name__}.\n"
                    f"Please modify the description or change the field name to a non-reserved name."
                    f"To get a full list of reserved descriptions, navigate to openbb_core.provider.utils.descriptions.py"
                    f"You can also add extra information to the existing reserved field description in your model."
                )
        elif name in DATA_DESCRIPTIONS:
            assert DATA_DESCRIPTIONS[name] in getattr(field, "description"), (
                f"Description for {name} is incorrect for the {standard_model.__name__}.\n"
                f"Please modify the description or change the field name to a non-reserved name."
                f"To get a full list of reserved descriptions, navigate to openbb_core.provider.utils.descriptions.py"
                f"You can also add extra information to the existing reserved field description in your model."
            )