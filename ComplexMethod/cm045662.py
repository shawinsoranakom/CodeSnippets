def concat(self, *others: Table[TSchema]) -> Table[TSchema]:
        """Concats `self` with every `other` ∊ `others`.

        Semantics:
        - result.columns == self.columns == other.columns
        - result.id == self.id ∪ other.id

        if self.id and other.id collide, throws an exception.

        Requires:
        - other.columns == self.columns
        - self.id disjoint with other.id

        Args:
            other:  the other table.

        Returns:
            Table: The concatenated table. Id's of rows from original tables are preserved.

        Example:

        >>> import pathway as pw
        >>> t1 = pw.debug.table_from_markdown('''
        ...   | age | owner | pet
        ... 1 | 10  | Alice | 1
        ... 2 | 9   | Bob   | 1
        ... 3 | 8   | Alice | 2
        ... ''')
        >>> t2 = pw.debug.table_from_markdown('''
        ...    | age | owner | pet
        ... 11 | 11  | Alice | 30
        ... 12 | 12  | Tom   | 40
        ... ''')
        >>> pw.universes.promise_are_pairwise_disjoint(t1, t2)
        >>> t3 = t1.concat(t2)
        >>> pw.debug.compute_and_print(t3, include_id=False)
        age | owner | pet
        8   | Alice | 2
        9   | Bob   | 1
        10  | Alice | 1
        11  | Alice | 30
        12  | Tom   | 40
        """
        for other in others:
            if other.keys() != self.keys():
                self_keys = set(self.keys())
                other_keys = set(other.keys())
                missing_keys = self_keys - other_keys
                superfluous_keys = other_keys - self_keys
                raise ValueError(
                    "columns do not match in the argument of Table.concat()."
                    + (
                        f" Missing columns: {missing_keys}."
                        if missing_keys is not None
                        else ""
                    )
                    + (
                        f" Superfluous columns: {superfluous_keys}."
                        if superfluous_keys is not None
                        else ""
                    )
                )
        schema = {}
        all_args: list[Table] = [self, *others]

        for key in self.keys():
            schema[key] = _types_lca_with_error(
                *[arg.schema._dtypes()[key] for arg in all_args],
                function_name="a concat",
                pointers=False,
                key=key,
            )
        id_type = _types_lca_with_error(
            *[arg.schema._id_dtype for arg in all_args],
            function_name="a concat",
            pointers=True,
        )

        return Table._concat(
            *[tab.cast_to_types(**schema).update_id_type(id_type) for tab in all_args]
        )