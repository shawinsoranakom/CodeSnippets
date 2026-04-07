def as_sqlite(self, compiler, connection):
        lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
        return self._process_as_sqlite(lhs, params, connection, key_transforms)