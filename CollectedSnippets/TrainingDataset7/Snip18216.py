def listener_logout(self, user, **kwargs):
        self.logged_out.append(user)