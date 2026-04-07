def identity(self):
        return (
            self.__class__,
            self.table_name,
            self.parent_alias,
            self.join_field,
            self.filtered_relation,
        )