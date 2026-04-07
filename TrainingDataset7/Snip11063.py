def _db_default_expression(self):
        db_default = self.db_default
        if self.has_db_default() and not hasattr(db_default, "resolve_expression"):
            from django.db.models.expressions import Value

            db_default = Value(db_default, self)
        return db_default