def test_serialize_functools_partial_posarg(self):
        value = functools.partial(datetime.timedelta, 1)
        string, imports = MigrationWriter.serialize(value)
        self.assertSerializedFunctoolsPartialEqual(
            value,
            "functools.partial(datetime.timedelta, 1)",
            {"import datetime", "import functools"},
        )