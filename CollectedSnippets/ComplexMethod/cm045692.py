def _compute_column_dependencies_ordinary(
        self,
        operator: Operator,
        scope_context: ScopeContext,
        column_dependencies: dict[Universe, StableSet[Column]],
    ) -> None:
        # reverse because we traverse the operators list backward
        # and want to process output tables before intermediate tables
        # because we want to propagate dependencies from output tables
        # to intermediate tables
        intermediate_and_output_tables_rev = reversed(
            list(operator.intermediate_and_output_tables)
        )

        for table in intermediate_and_output_tables_rev:
            output_deps: StableSet[Column] = StableSet()
            # set columns that have to be produced
            output_deps.update(column_dependencies.get(table._universe, []))
            # columns tree shaking if set to False
            if scope_context.run_all:
                output_deps.update(table._columns.values())
            self.column_deps_at_output[operator][table] = output_deps

            # add column dependencies
            for column in chain(table._columns.values(), [table._id_column]):
                # if the first condition is not met, the column is not needed (tree shaking)
                if column in output_deps or isinstance(column, IdColumn):
                    for dependency in column.column_dependencies():
                        if not isinstance(dependency, IdColumn):
                            column_dependencies[dependency.universe].add(dependency)

            # remove current columns (they are created in this operator)
            column_dependencies[table._universe] -= StableSet(table._columns.values())

        for table in operator.hard_table_dependencies():
            column_dependencies[table._universe].update(table._columns.values())