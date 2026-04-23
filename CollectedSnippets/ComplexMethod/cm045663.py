def rename_columns(self, **kwargs: str | expr.ColumnReference) -> Table:
        """Rename columns according to kwargs.

        Columns not in keys(kwargs) are not changed. New name of a column must not be `id`.

        Args:
            kwargs:  mapping from old column names to new names.

        Returns:
            Table: `self` with columns renamed.

        Example:

        >>> import pathway as pw
        >>> t1 = pw.debug.table_from_markdown('''
        ... age | owner | pet
        ... 10  | Alice | 1
        ... 9   | Bob   | 1
        ... 8   | Alice | 2
        ... ''')
        >>> t2 = t1.rename_columns(years_old=t1.age, animal=t1.pet)
        >>> pw.debug.compute_and_print(t2, include_id=False)
        owner | years_old | animal
        Alice | 8         | 2
        Alice | 10        | 1
        Bob   | 9         | 1
        """
        mapping: dict[str, str] = {}
        for new_name, old_name_col in kwargs.items():
            if isinstance(old_name_col, expr.ColumnReference):
                old_name = old_name_col.name
            else:
                old_name = old_name_col
            if old_name not in self._columns:
                raise ValueError(f"Column {old_name} does not exist in a given table.")
            mapping[new_name] = old_name
        renamed_columns = self._columns.copy()
        for new_name, old_name in mapping.items():
            renamed_columns.pop(old_name)
        for new_name, old_name in mapping.items():
            renamed_columns[new_name] = self._columns[old_name]

        columns_wrapped = {
            name: self._wrap_column_in_context(
                self._rowwise_context,
                column,
                mapping[name] if name in mapping else name,
            )
            for name, column in renamed_columns.items()
        }
        return self._with_same_universe(*columns_wrapped.items())