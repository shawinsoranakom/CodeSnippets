def test_serialize_functools_partial_non_identifier_keyword(self):
        value = functools.partial(datetime.timedelta, **{"kebab-case": 1})
        string, imports = MigrationWriter.serialize(value)
        self.assertSerializedFunctoolsPartialEqual(
            value,
            "functools.partial(datetime.timedelta, **{'kebab-case': 1})",
            {"import datetime", "import functools"},
        )