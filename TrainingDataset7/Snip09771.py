def _column_generated_persistency_sql(self, field):
        return "MATERIALIZED" if field.db_persist else "VIRTUAL"