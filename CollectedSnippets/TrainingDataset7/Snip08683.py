def _add_attachment(self, msg, filename, content, mimetype):
        encoding = self.encoding or settings.DEFAULT_CHARSET
        maintype, subtype = mimetype.split("/", 1)

        if maintype == "text" and isinstance(content, bytes):
            # This duplicates logic from EmailMessage.attach() to properly
            # handle EmailMessage.attachments not created through attach().
            try:
                content = content.decode()
            except UnicodeDecodeError:
                mimetype = DEFAULT_ATTACHMENT_MIME_TYPE
                maintype, subtype = mimetype.split("/", 1)

        # See email.contentmanager.set_content() docs for the cases here.
        if maintype == "text":
            # For text/*, content must be str, and maintype cannot be provided.
            msg.add_attachment(
                content, subtype=subtype, filename=filename, charset=encoding
            )
        elif maintype == "message":
            # For message/*, content must be email.message.EmailMessage (or
            # legacy email.message.Message), and maintype cannot be provided.
            if isinstance(content, EmailMessage):
                # Django EmailMessage.
                content = content.message(policy=msg.policy)
            elif not isinstance(
                content, (email.message.EmailMessage, email.message.Message)
            ):
                content = email.message_from_bytes(
                    force_bytes(content), policy=msg.policy
                )
            msg.add_attachment(content, subtype=subtype, filename=filename)
        else:
            # For all other types, content must be bytes-like, and both
            # maintype and subtype must be provided.
            if not isinstance(content, (bytes, bytearray, memoryview)):
                content = force_bytes(content)
            msg.add_attachment(
                content,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )