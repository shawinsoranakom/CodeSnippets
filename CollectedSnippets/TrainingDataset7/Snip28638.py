def test_expressions_and_fields_mutually_exclusive(self):
        msg = "Index.fields and expressions are mutually exclusive."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(Upper("foo"), fields=["field"])