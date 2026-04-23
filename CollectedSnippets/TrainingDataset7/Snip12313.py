def final_transformer(field, alias):
            if not self.alias_cols:
                alias = None
            return field.get_col(alias)