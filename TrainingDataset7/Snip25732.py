def send_mail(self, subject, message, *args, **kwargs):
                mail.mail_managers(
                    subject, message, *args, connection=self.connection(), **kwargs
                )