def test_no_objects(self):
        """
        The default manager, "objects", doesn't exist, because a custom one
        was provided.
        """
        msg = "type object 'Book' has no attribute 'objects'"
        with self.assertRaisesMessage(AttributeError, msg):
            Book.objects