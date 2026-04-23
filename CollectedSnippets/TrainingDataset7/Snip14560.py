def send_mail(self, subject, message, *args, **kwargs):
        mail.mail_admins(
            subject, message, *args, connection=self.connection(), **kwargs
        )