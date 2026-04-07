def _add_bodies(self, msg):
        if self.body or not self.attachments:
            encoding = self.encoding or settings.DEFAULT_CHARSET
            body = force_str(
                self.body or "", encoding=encoding, errors="surrogateescape"
            )
            msg.set_content(body, subtype=self.content_subtype, charset=encoding)