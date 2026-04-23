def test_serialize_functools_partialmethod(self):
        value = functools.partialmethod(datetime.timedelta, 1, seconds=2)
        string, imports = MigrationWriter.serialize(value)
        result = self.assertSerializedFunctoolsPartialEqual(
            value,
            "functools.partialmethod(datetime.timedelta, 1, seconds=2)",
            {"import datetime", "import functools"},
        )
        self.assertIsInstance(result, functools.partialmethod)