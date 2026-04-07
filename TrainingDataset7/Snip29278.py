def test_hidden_accessor(self):
        """
        When a '+' ending related name is specified no reverse accessor should
        be added to the related model.
        """
        self.assertFalse(
            hasattr(
                Target,
                HiddenPointer._meta.get_field("target").remote_field.accessor_name,
            )
        )