def _text_repr(self, content, force_string):
        if isinstance(content, bytes) and not force_string:
            return safe_repr(content)
        return "'%s'" % str(content)