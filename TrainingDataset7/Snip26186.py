def flush_mailbox(self):
        raise NotImplementedError(
            "subclasses of BaseEmailBackendTests may require a flush_mailbox() method"
        )