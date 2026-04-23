def test_deconstruct(self):
        field = models.CharField()
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {})
        field = models.CharField(db_collation="utf8_esperanto_ci")
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {"db_collation": "utf8_esperanto_ci"})