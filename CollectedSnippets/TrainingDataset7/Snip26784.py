def setUpClass(cls):
        # Simulate another TransactionTestCase having just torn down.
        call_command("flush", verbosity=0, interactive=False, allow_cascade=True)
        super().setUpClass()
        cls.book = Book.objects.first()