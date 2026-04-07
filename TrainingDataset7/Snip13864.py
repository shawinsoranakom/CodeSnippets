def _pre_setup(cls):
        """
        Perform pre-test setup:
        * Create a test client.
        * Clear the mail test outbox.
        """
        cls.client = cls.client_class()
        cls.async_client = cls.async_client_class()
        mail.outbox = []