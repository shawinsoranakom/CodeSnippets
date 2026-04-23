def assertSkippedDatabases(self, test_labels, expected_databases):
        databases, output = self.get_databases(test_labels)
        self.assertEqual(databases, expected_databases)
        skipped_databases = set(connections) - set(expected_databases)
        if skipped_databases:
            self.assertIn(self.skip_msg + ", ".join(sorted(skipped_databases)), output)
        else:
            self.assertNotIn(self.skip_msg, output)