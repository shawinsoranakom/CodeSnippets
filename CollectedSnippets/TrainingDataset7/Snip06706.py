def __conform__(self, protocol):
        if protocol is Database.PrepareProtocol:
            return str(self)