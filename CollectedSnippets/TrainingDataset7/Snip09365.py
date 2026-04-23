def _column_generated_persistency_sql(self, field):
        """Return the SQL to define the persistency of generated fields."""
        return "STORED" if field.db_persist else "VIRTUAL"