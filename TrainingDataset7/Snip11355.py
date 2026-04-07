def as_oracle(self, compiler, connection):
        lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
        return self._process_as_oracle(lhs, params, connection, key_transforms)