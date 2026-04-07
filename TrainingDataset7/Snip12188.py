def relabeled_clone(self, change_map):
        new_parent_alias = change_map.get(self.parent_alias, self.parent_alias)
        new_table_alias = change_map.get(self.table_alias, self.table_alias)
        if self.filtered_relation is not None:
            filtered_relation = self.filtered_relation.relabeled_clone(change_map)
        else:
            filtered_relation = None
        return self.__class__(
            self.table_name,
            new_parent_alias,
            new_table_alias,
            self.join_type,
            self.join_field,
            self.nullable,
            filtered_relation=filtered_relation,
        )