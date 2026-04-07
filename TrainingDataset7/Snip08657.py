def connection_class(self):
        return smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP