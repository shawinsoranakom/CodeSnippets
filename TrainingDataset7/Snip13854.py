def __call__(self):
        raise DatabaseOperationForbidden(self.message)