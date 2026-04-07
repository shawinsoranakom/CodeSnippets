def hook():
            self.callback_called = True
            raise MyException("robust callback")