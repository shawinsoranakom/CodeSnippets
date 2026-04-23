def test_save(self):
        msg = "RequestSite cannot be saved."
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.site.save()