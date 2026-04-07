def test_raises_exception(self):
        class MyException(Exception):
            pass

        # Create an exception
        try:
            raise MyException("Test Message")
        except MyException:
            exc_info = sys.exc_info()

        with mock.patch("django.utils.autoreload._exception", exc_info):
            with self.assertRaisesMessage(MyException, "Test Message"):
                autoreload.raise_last_exception()