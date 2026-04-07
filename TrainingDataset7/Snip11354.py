def as_mysql(self, compiler, connection):
        lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
        return self._process_as_mysql(lhs, params, connection, key_transforms)