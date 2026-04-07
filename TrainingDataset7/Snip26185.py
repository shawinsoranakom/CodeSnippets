def get_mailbox_content(self):
        raise NotImplementedError(
            "subclasses of BaseEmailBackendTests must provide a get_mailbox_content() "
            "method"
        )