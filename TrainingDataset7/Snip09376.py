def remove_constraint(self, model, constraint):
        """Remove a constraint from a model."""
        sql = constraint.remove_sql(model, self)
        if sql:
            self.execute(sql)