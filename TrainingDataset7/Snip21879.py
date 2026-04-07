def test_delete_no_name(self):
        """
        Calling delete with an empty name should not try to remove the base
        storage directory, but fail loudly (#20660).
        """
        msg = "The name must be given to delete()."
        with self.assertRaisesMessage(ValueError, msg):
            self.storage.delete(None)
        with self.assertRaisesMessage(ValueError, msg):
            self.storage.delete("")