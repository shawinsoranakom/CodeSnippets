def listener_login_failed(self, sender, **kwargs):
        self.login_failed.append(kwargs)