def relabeled_clone(self, change_map):
        return self.__class__(
            self.table_name, change_map.get(self.table_alias, self.table_alias)
        )