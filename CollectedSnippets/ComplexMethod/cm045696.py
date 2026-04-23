def compute(
        self,
        output_columns: Iterable[clmn.Column],
        input_storages: dict[Universe, Storage],
        table_columns: Iterable[clmn.Column],
    ) -> Storage:
        context = self.context
        output_columns_list = list(output_columns)
        source_universe = context.union_ids[0].universe
        # ensure that keeping structure is possible,
        # i.e. all sources have the same path to required columns
        keep_structure = True
        for column in output_columns_list:
            assert isinstance(column, clmn.ColumnWithReference)
            source_column = column.expression._column
            path = input_storages[source_column.universe].get_path(source_column)
            for dep in column.reference_column_dependencies():
                if input_storages[dep.universe].get_path(dep) != path:
                    keep_structure = False
                    break
            if not keep_structure:
                break

        if isinstance(context, clmn.ConcatUnsafeContext):
            updates = context.updates
        else:
            updates = (context.updates,)

        names = []
        source_columns: list[list[clmn.Column]] = [[]]
        for column in output_columns_list:
            assert isinstance(column, clmn.ColumnWithExpression)
            assert isinstance(column.expression, expr.ColumnReference)
            names.append(column.expression.name)
            source_columns[0].append(column.dereference())
        for columns in updates:
            source_columns.append([columns[name] for name in names])

        if keep_structure and isinstance(context, clmn.UpdateRowsContext):
            for universe, cols in zip(
                self.context.universe_dependencies(), source_columns, strict=True
            ):
                input_storage = input_storages[universe]
                maybe_flat_storage = maybe_flatten_input_storage(input_storage, cols)
                if maybe_flat_storage is not input_storage:
                    keep_structure = False
                    break

        flattened_inputs = {}
        for i, (universe, cols) in enumerate(
            zip(self.context.universe_dependencies(), source_columns, strict=True)
        ):
            if keep_structure:
                flattened_storage = input_storages[universe]
            else:
                flattened_storage = Storage.flat(universe, cols)

            flattened_inputs[f"{i}"] = flattened_storage

        evaluator: PathEvaluator
        if keep_structure:
            evaluator = NoNewColumnsPathEvaluator(context)
        else:
            evaluator = FlatStoragePathEvaluator(context)

        storage = evaluator.compute(
            output_columns_list,
            {source_universe: input_storages[source_universe]},
            table_columns,
        )

        return storage.with_maybe_flattened_inputs(flattened_inputs)