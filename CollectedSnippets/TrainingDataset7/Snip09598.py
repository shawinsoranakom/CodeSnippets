def _alter_column_comment_sql(self, model, new_field, new_type, new_db_comment):
        # Comment is alter when altering the column type.
        return "", []