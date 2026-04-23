def _get_colref_by_name(
        self,
        name: str,
        exception_type,
    ) -> expr.ColumnReference:
        name = self._column_deprecation_rename(name)
        if name == "id":
            return self._inner_table.id
        elif name in self._joined_on_names:
            if self._join_mode is JoinMode.INNER:
                return self._original_left[name]
            else:
                return self._inner_table[name]
        elif name in self._original_left.keys() and name in self._original_right.keys():
            raise exception_type(
                f"Column {name} appears on both left and right inputs of join."
            )
        elif name in self._original_left.keys():
            return self._original_left[name]
        elif name in self._original_right.keys():
            return self._original_right[name]
        else:
            raise exception_type(f"No column with name {name}.")