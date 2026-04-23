def _is_text_or_blob(self, field):
        db_type = field.db_type(self.connection)
        return db_type and db_type.lower().endswith(("blob", "text"))