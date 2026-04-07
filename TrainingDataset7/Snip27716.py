def test_serialize_functools_partial(self):
        value = functools.partial(datetime.timedelta)
        string, imports = MigrationWriter.serialize(value)
        self.assertSerializedFunctoolsPartialEqual(
            value,
            "functools.partial(datetime.timedelta)",
            {"import datetime", "import functools"},
        )