def setUpClass(cls):
        cls.check_allowed_hosts(["testserver"])
        try:
            super().setUpClass()
        except RuntimeError:
            # LiveServerTestCase's change to ALLOWED_HOSTS should be reverted.
            cls.doClassCleanups()
            cls.check_allowed_hosts(["testserver"])
        else:
            raise RuntimeError("Server did not fail.")
        cls.set_up_called = True