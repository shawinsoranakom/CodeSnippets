def test_expressions_requires_index_name(self):
        msg = "An index must be named to use expressions."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(Lower("field"))