def encode_utf8(self, command):
        if six.PY2:
            return command.encode('utf8')
        return command