def _compute_storage_paths_iterate(
        self, operator: IterateOperator, storages: dict[Universe, Storage]
    ) -> None:
        # for iterate, the structure of input tables has to be the same as the structure
        # of corresponding output tables so that iterate can finish.
        # the only structure changes can be done before input or after output.
        inner_column_paths: dict[Universe, dict[Column, ColumnPath]] = defaultdict(dict)
        outer_tables = (
            operator.iterated + operator.iterated_with_universe + operator.extra
        )
        inner_tables = (
            operator.iterated_copy
            + operator.iterated_with_universe_copy
            + operator.extra_copy
        )
        # map paths of outer columns to paths of inner columns
        for name, outer_table in outer_tables.items():
            assert isinstance(outer_table, Table)
            inner_table = inner_tables[name]
            assert isinstance(inner_table, Table)
            storage = storages[outer_table._universe]
            for column_name, outer_column in outer_table._columns.items():
                inner_column = inner_table._columns[column_name]
                path = storage.get_path(outer_column)
                inner_column_paths[inner_table._universe][inner_column] = path

        for universe, paths in inner_column_paths.items():
            self.iterate_subgraphs[operator].initial_storages[universe] = Storage.flat(
                universe, paths.keys()
            )

        self.iterate_subgraphs[operator]._compute_storage_paths()

        # propagate paths over iterate (not looking inside)
        for name, handle in operator._outputs.items():
            table = handle.value
            output_columns = self.column_deps_at_output[operator][table]
            input_table = operator.get_input(name).value
            assert isinstance(input_table, Table)
            path_storage = Storage.flat(table._universe, output_columns)
            self.output_storages[operator][table] = path_storage
            storages[table._universe] = path_storage