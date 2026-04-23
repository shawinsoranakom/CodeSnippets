def test_13_valid_dict_annotation(self):
        """
        Tests to make sure that `dict` based annotations
        are correctly made in the `TrainingArguments`.

        If this fails, a type annotation change is
        needed on a new input
        """
        base_list = TrainingArguments._VALID_DICT_FIELDS.copy()
        args = TrainingArguments

        # First find any annotations that contain `dict`
        fields = args.__dataclass_fields__

        raw_dict_fields = []
        optional_dict_fields = []

        for field_ in fields.values():
            # First verify raw dict
            if field_.type is dict:
                raw_dict_fields.append(field_)
            # Next check for `Union` or `Optional`
            elif get_origin(field_.type) == Union:
                if any(arg is dict for arg in get_args(field_.type)):
                    optional_dict_fields.append(field_)

        # First check: anything in `raw_dict_fields` is very bad
        self.assertEqual(
            len(raw_dict_fields),
            0,
            f"Found invalid raw `dict` types in the `TrainingArgument` typings, which are {raw_dict_fields}. "
            "This leads to issues with the CLI. Please turn this into `typing.Optional[dict,str]`",
        )

        # Next check raw annotations
        for field_ in optional_dict_fields:
            args = get_args(field_.type)
            # These should be returned as `dict`, `str`, ...
            # we only care about the first two
            self.assertIn(
                dict,
                args,
                f"Expected field `{field_.name}` to have a type signature of at least `typing.Union[dict,str,...]` for CLI compatibility, but `dict` not found. Please fix this.",
            )
            self.assertIn(
                str,
                args,
                f"Expected field `{field_.name}` to have a type signature of at least `typing.Union[dict,str,...]` for CLI compatibility, but `str` not found. Please fix this.",
            )

        # Second check: anything in `optional_dict_fields` is bad if it's not in `base_list`
        for field_ in optional_dict_fields:
            self.assertIn(
                field.name,
                base_list,
                f"Optional dict field `{field_.name}` is not in the base list of valid fields. Please add it to `TrainingArguments._VALID_DICT_FIELDS`",
            )