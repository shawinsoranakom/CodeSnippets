def test_double_call_autodiscover(self):
        # The first time autodiscover is called, we should get our real error.
        with self.assertRaisesMessage(Exception, "Bad admin module"):
            admin.autodiscover()
        # Calling autodiscover again should raise the very same error it did
        # the first time, not an AlreadyRegistered error.
        with self.assertRaisesMessage(Exception, "Bad admin module"):
            admin.autodiscover()