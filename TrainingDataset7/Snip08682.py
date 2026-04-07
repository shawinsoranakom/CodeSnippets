def _add_attachments(self, msg):
        if self.attachments:
            if hasattr(self, "mixed_subtype"):
                # RemovedInDjango70Warning.
                raise AttributeError(
                    "EmailMessage no longer supports the"
                    " undocumented `mixed_subtype` attribute"
                )
            msg.make_mixed()
            for attachment in self.attachments:
                if isinstance(attachment, email.message.MIMEPart):
                    msg.attach(attachment)
                elif isinstance(attachment, MIMEBase):
                    # RemovedInDjango70Warning.
                    msg.attach(attachment)
                else:
                    self._add_attachment(msg, *attachment)