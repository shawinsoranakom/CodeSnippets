def get_decoded_attachments(self, django_message):
        """
        Return a list of decoded attachments resulting from serializing
        django_message and reparsing the result.

        Each attachment is returned as an EmailAttachment named tuple with
        fields filename, content, and mimetype. The content will be decoded
        to str for mimetype text/*; retained as bytes for other mimetypes.
        """
        return [
            EmailAttachment(
                attachment.get_filename(),
                attachment.get_content(),
                attachment.get_content_type(),
            )
            for attachment in self.get_raw_attachments(django_message)
        ]