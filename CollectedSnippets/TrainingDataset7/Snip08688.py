def _add_bodies(self, msg):
        if self.body or not self.alternatives:
            super()._add_bodies(msg)
        if self.alternatives:
            if hasattr(self, "alternative_subtype"):
                # RemovedInDjango70Warning.
                raise AttributeError(
                    "EmailMultiAlternatives no longer supports the"
                    " undocumented `alternative_subtype` attribute"
                )
            msg.make_alternative()
            encoding = self.encoding or settings.DEFAULT_CHARSET
            for alternative in self.alternatives:
                maintype, subtype = alternative.mimetype.split("/", 1)
                content = alternative.content
                if maintype == "text":
                    if isinstance(content, bytes):
                        content = content.decode()
                    msg.add_alternative(content, subtype=subtype, charset=encoding)
                else:
                    content = force_bytes(content, encoding=encoding, strings_only=True)
                    msg.add_alternative(content, maintype=maintype, subtype=subtype)
        return msg