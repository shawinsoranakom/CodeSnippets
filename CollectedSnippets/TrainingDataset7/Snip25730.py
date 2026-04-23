def my_mail_admins(*args, **kwargs):
            connection = kwargs["connection"]
            self.assertIsInstance(connection, MyEmailBackend)
            mail_admins_called["called"] = True