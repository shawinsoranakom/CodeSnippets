def decode_utf8(self, command_parts):
        if six.PY2:
            return [s.decode('utf8') for s in command_parts]
        return command_parts