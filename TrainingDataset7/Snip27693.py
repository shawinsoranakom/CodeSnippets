def test_serialize_nested_class_method(self):
        self.assertSerializedResultEqual(
            self.NestedChoices.method,
            (
                "migrations.test_writer.WriterTests.NestedChoices.method",
                {"import migrations.test_writer"},
            ),
        )