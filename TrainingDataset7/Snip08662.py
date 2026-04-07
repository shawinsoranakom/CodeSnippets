def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        from_email = self.prep_address(email_message.from_email)
        recipients = [self.prep_address(addr) for addr in email_message.recipients()]
        message = email_message.message(policy=email.policy.SMTP)
        try:
            self.connection.sendmail(from_email, recipients, message.as_bytes())
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True