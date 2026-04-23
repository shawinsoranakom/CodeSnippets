def as_sql(self, compiler, connection):
                lhs, lhs_params = self.process_lhs(compiler, connection)
                rhs, rhs_params = self.process_rhs(compiler, connection)
                # Although combining via (*lhs_params, *rhs_params) would be
                # more resilient, the "simple" way works too.
                params = lhs_params + rhs_params
                return "%s <> %s" % (lhs, rhs), params