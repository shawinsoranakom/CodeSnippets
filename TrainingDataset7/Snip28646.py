def test_include_requires_list_or_tuple(self):
        msg = "Index.include must be a list or tuple."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(name="test_include", fields=["field"], include="other")