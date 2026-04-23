def test_parse_number(self):
        tests = [
            ("no_number", None),
            ("0001_initial", 1),
            ("0002_model3", 2),
            ("0002_auto_20380101_1112", 2),
            ("0002_squashed_0003", 3),
            ("0002_model2_squashed_0003_other4", 3),
            ("0002_squashed_0003_squashed_0004", 4),
            ("0002_model2_squashed_0003_other4_squashed_0005_other6", 5),
            ("0002_custom_name_20380101_1112_squashed_0003_model", 3),
            ("2_squashed_4", 4),
        ]
        for migration_name, expected_number in tests:
            with self.subTest(migration_name=migration_name):
                self.assertEqual(
                    MigrationAutodetector.parse_number(migration_name),
                    expected_number,
                )