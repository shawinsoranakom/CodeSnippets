def groupby(
        self,
        *args: expr.ColumnReference,
        id: expr.ColumnReference | None = None,
        sort_by: expr.ColumnReference | None = None,
        _filter_out_results_of_forgetting: bool = False,
        instance: expr.ColumnReference | None = None,
        _skip_errors: bool = True,
        _is_window: bool = False,
    ) -> groupbys.GroupedTable:
        """Groups table by columns from args.

        Note:
            Usually followed by `.reduce()` that aggregates the result and returns a table.

        Args:
            args: columns to group by.
            id: if provided, is the column used to set id's of the rows of the result
            sort_by: if provided, column values are used as sorting keys for particular reducers
            instance: optional argument describing partitioning of the data into separate instances

        Returns:
            GroupedTable: Groupby object.

        Example:

        >>> import pathway as pw
        >>> t1 = pw.debug.table_from_markdown('''
        ... age | owner | pet
        ... 10  | Alice | dog
        ... 9   | Bob   | dog
        ... 8   | Alice | cat
        ... 7   | Bob   | dog
        ... ''')
        >>> t2 = t1.groupby(t1.pet, t1.owner).reduce(t1.owner, t1.pet, ageagg=pw.reducers.sum(t1.age))
        >>> pw.debug.compute_and_print(t2, include_id=False)
        owner | pet | ageagg
        Alice | cat | 8
        Alice | dog | 10
        Bob   | dog | 16
        """
        if instance is not None:
            args = (*args, instance)
        if id is not None:
            if len(args) == 0:
                args = (id,)
            elif len(args) > 1:
                raise ValueError(
                    "Table.groupby() cannot have id argument when grouping by multiple columns."
                )
            elif args[0]._column != id._column:
                raise ValueError(
                    "Table.groupby() received id argument and is grouped by a single column,"
                    + " but the arguments are not equal.\n"
                    + "Consider using <table>.groupby(id=...), skipping the positional argument."
                )

        for arg in args:
            if not isinstance(arg, expr.ColumnReference):
                if isinstance(arg, str):
                    raise ValueError(
                        f"Expected a ColumnReference, found a string. Did you mean <table>.{arg}"
                        + f" instead of {repr(arg)}?"
                    )
                else:
                    raise ValueError(
                        "All Table.groupby() arguments have to be a ColumnReference."
                    )

        self._check_for_disallowed_types(*args)
        return groupbys.GroupedTable.create(
            table=self,
            grouping_columns=args,
            last_column_is_instance=instance is not None,
            set_id=id is not None,
            sort_by=sort_by,
            _filter_out_results_of_forgetting=_filter_out_results_of_forgetting,
            _skip_errors=_skip_errors,
            _is_window=_is_window,
        )