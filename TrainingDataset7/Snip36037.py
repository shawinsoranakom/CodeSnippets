def test_raises_custom_exception(self):
        class MyException(Exception):
            def __init__(self, msg, extra_context):
                super().__init__(msg)
                self.extra_context = extra_context

        # Create an exception.
        try:
            raise MyException("Test Message", "extra context")
        except MyException:
            exc_info = sys.exc_info()

        with mock.patch("django.utils.autoreload._exception", exc_info):
            with self.assertRaisesMessage(MyException, "Test Message"):
                autoreload.raise_last_exception()