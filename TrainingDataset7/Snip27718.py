def test_serialize_functools_partial_kwarg(self):
        value = functools.partial(datetime.timedelta, seconds=2)
        string, imports = MigrationWriter.serialize(value)
        self.assertSerializedFunctoolsPartialEqual(
            value,
            "functools.partial(datetime.timedelta, seconds=2)",
            {"import datetime", "import functools"},
        )