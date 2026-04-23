def test_include_requires_index_name(self):
        msg = "A covering index must be named."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(fields=["field"], include=["other"])