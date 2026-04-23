def raise_error(self):
        raise NodeNotFoundError(self.error_message, self.key, origin=self.origin)