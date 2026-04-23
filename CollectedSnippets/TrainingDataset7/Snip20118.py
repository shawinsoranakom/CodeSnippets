def as_oracle(self, compiler, connection, **extra_context):
        lhs, lhs_params = compiler.compile(self.lhs)
        return "mod(%s, 3)" % lhs, lhs_params