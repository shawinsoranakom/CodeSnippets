def test_delete(self):
        msg = "RequestSite cannot be deleted."
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.site.delete()