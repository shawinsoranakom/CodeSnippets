def get_raw_attachments(self, django_message):
        """
        Return a list of the raw attachment parts in the MIME message generated
        by serializing django_message and reparsing the result.

        This returns only "top-level" attachments. It will not descend into
        message/* attached emails to find nested attachments.
        """
        msg_bytes = django_message.message().as_bytes()
        message = message_from_bytes(msg_bytes)
        return list(message.iter_attachments())