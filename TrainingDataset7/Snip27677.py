def assertSerializedResultEqual(self, value, target):
        self.assertEqual(MigrationWriter.serialize(value), target)