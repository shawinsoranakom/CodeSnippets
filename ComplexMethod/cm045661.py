def ix(
        self,
        expression: expr.ColumnExpression,
        *,
        optional: bool = False,
        context=None,
        allow_misses: bool = False,
    ) -> Table:
        """Reindexes the table using expression values as keys. Uses keys from context, or tries to infer
        proper context from the expression.
        If optional is True, then None in expression values result in None values in the result columns.
        Missing values in table keys result in RuntimeError.
        If ``allow_misses`` is set to True, they result in None value on the output.

        Context can be anything that allows for `select` or `reduce`, or `pathway.this` construct
        (latter results in returning a delayed operation, and should be only used when using `ix` inside
        join().select() or groupby().reduce() sequence).

        Returns:
            Reindexed table with the same set of columns.

        Example:

        >>> import pathway as pw
        >>> t_animals = pw.debug.table_from_markdown('''
        ...   | epithet    | genus
        ... 1 | upupa      | epops
        ... 2 | acherontia | atropos
        ... 3 | bubo       | scandiacus
        ... 4 | dynastes   | hercules
        ... ''')
        >>> t_birds = pw.debug.table_from_markdown('''
        ...   | desc
        ... 2 | hoopoe
        ... 4 | owl
        ... ''')
        >>> ret = t_birds.select(t_birds.desc, latin=t_animals.ix(t_birds.id).genus)
        >>> pw.debug.compute_and_print(ret, include_id=False)
        desc   | latin
        hoopoe | atropos
        owl    | hercules
        """

        if context is None:
            all_tables = collect_tables(expression)
            if len(all_tables) == 0:
                context = thisclass.this
            elif all(tab == all_tables[0] for tab in all_tables):
                context = all_tables[0]
        if context is None:
            for tab in all_tables:
                if not isinstance(tab, Table):
                    raise ValueError("Table expected here.")
            if len(all_tables) == 0:
                raise ValueError("Const value provided.")
            context = all_tables[0]
            for tab in all_tables:
                assert context._universe.is_equal_to(tab._universe)
        if isinstance(context, groupbys.GroupedJoinable):
            context = thisclass.this
        if isinstance(context, thisclass.ThisMetaclass):
            return context._delayed_op(
                lambda table, expression: self.ix(
                    expression=expression,
                    optional=optional,
                    context=table,
                    allow_misses=allow_misses,
                ),
                expression=expression,
                qualname=f"{self}.ix(...)",
                name="ix",
            )
        restrict_universe = RestrictUniverseDesugaring(context)
        expression = restrict_universe.eval_expression(expression)
        key_tab = context.select(tmp=expression)
        key_col = key_tab.tmp
        key_dtype = key_tab.eval_type(key_col)
        supertype = dt.ANY_POINTER
        if optional:
            supertype = dt.Optional(supertype)
        if not dt.dtype_issubclass(key_dtype, supertype):
            raise TypeError(
                f"Pathway supports indexing with Pointer type only. The type used was {key_dtype}."
            )
        supertype = self._id_column.dtype
        if optional:
            supertype = dt.Optional(supertype)
        if not dt.dtype_issubclass(key_dtype, supertype):
            raise TypeError(
                "Indexing a table with a Pointer type with probably mismatched primary keys."
                + f" Type used was {key_dtype}. Indexed id type was {supertype}."
            )
        if optional and isinstance(key_dtype, dt.Optional):
            self_ = self.update_types(
                **{name: dt.Optional(self.typehints()[name]) for name in self.keys()}
            )
        else:
            self_ = self
        if allow_misses:
            subset = self_._having(key_col)
            new_key_col = key_tab.restrict(subset).tmp
            fill = key_tab.difference(subset).select(
                **{name: None for name in self.column_names()}
            )
            return Table.concat(
                self_._ix(new_key_col, optional=optional), fill
            ).with_universe_of(key_tab)

        else:
            return self_._ix(key_col, optional)