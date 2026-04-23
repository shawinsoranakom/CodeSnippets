def _compute_column_dependencies_iterate(self, operator: IterateOperator) -> None:
        inner_column_dependencies: dict[Universe, StableSet[Column]] = defaultdict(
            StableSet
        )
        all_columns: dict[Universe, StableSet[Column]] = defaultdict(StableSet)
        output_tables_columns: dict[Universe, StableSet[Column]] = defaultdict(
            StableSet
        )
        # propagate columns existing in iterate
        for name, outer_handle in operator._outputs.items():
            outer_table = outer_handle.value
            if name in operator.result_iterated:
                inner_table = operator.result_iterated[name]
            else:
                inner_table = operator.result_iterated_with_universe[name]
            assert isinstance(inner_table, Table)
            inner_deps = inner_column_dependencies[inner_table._universe]
            for column_name, outer_column in outer_table._columns.items():
                output_tables_columns[outer_table._universe].add(outer_column)
                inner_column = inner_table._columns[column_name]
                inner_deps.update([inner_column])

            if name in operator.result_iterated:
                all_columns[outer_table._universe].update(
                    self.column_deps_at_output[operator][outer_table]
                )

        inner_tables = (
            operator.iterated_copy
            + operator.iterated_with_universe_copy
            + operator.extra_copy
        )
        # input_universes - so that we know inside which universes are available
        # on iterate input
        input_universes: StableSet[Universe] = StableSet()
        for table in inner_tables.values():
            assert isinstance(table, Table)
            input_universes.add(table._universe)

        self.iterate_subgraphs[operator]._compute_relevant_columns(
            inner_column_dependencies, input_universes
        )