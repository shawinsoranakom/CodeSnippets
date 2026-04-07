def get_admin_email_handler(self, logger):
        # AdminEmailHandler does not get filtered out
        # even with DEBUG=True.
        return [
            h for h in logger.handlers if h.__class__.__name__ == "AdminEmailHandler"
        ][0]