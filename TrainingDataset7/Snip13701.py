def error(self, msg):
        raise HTMLParseError(msg, self.getpos())