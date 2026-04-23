def run(
        self,
        output_storage: Storage,
        old_path: ColumnPath | None = ColumnPath.EMPTY,
        disable_runtime_typechecking: bool = False,
    ) -> api.Table:
        input_storage = self.state.get_storage(self.context.universe)
        engine_input_table = self.state.get_table(input_storage._universe)
        if output_storage.has_only_references:
            return engine_input_table

        expressions = []
        eval_state = RowwiseEvalState()

        if (
            old_path is not None and not output_storage.has_only_new_columns
        ):  # keep old columns if they are needed
            placeholder_column = clmn.MaterializedColumn(
                self.context.universe,
                ColumnProperties(dtype=dt.ANY, append_only=input_storage.append_only),
            )
            expressions.append(
                api.ExpressionData(
                    self.eval_dependency(placeholder_column, eval_state=eval_state),
                    self.scope.table_properties(engine_input_table, old_path),
                    append_only=input_storage.append_only,
                    deterministic=True,
                )
            )
            input_storage = input_storage.with_updated_paths(
                {placeholder_column: old_path}
            )

        for column in output_storage.get_columns():
            if input_storage.has_column(column):
                continue
            assert isinstance(column, clmn.ColumnWithExpression)
            expression = column.expression
            expression = self.context.expression_with_type(expression)
            if (
                self.scope_context.runtime_typechecking
                and not disable_runtime_typechecking
            ):
                expression = TypeVerifier().eval_expression(expression)
            properties = api.TableProperties.column(self.column_properties(column))

            eval_state.reset_locally_deterministic()
            engine_expression = self.eval_expression(expression, eval_state=eval_state)
            append_only = column.properties.append_only
            deterministic = eval_state.locally_deterministic
            assert ColumnPath((len(expressions),)) == output_storage.get_path(column)
            expressions.append(
                api.ExpressionData(
                    engine_expression, properties, append_only, deterministic
                )
            )

        # START solution for eval_fully_async_apply
        for intermediate_storage in eval_state.storages:
            properties = self._table_properties(intermediate_storage)
            # restrict instead of override because of edge case in fully async UDF
            # with missing rows.
            engine_input_table = self.scope.restrict_table(
                engine_input_table,
                eval_state.get_temporary_table(intermediate_storage),
                properties,
            )
            input_storage = Storage.merge_storages(
                self.context.universe, intermediate_storage, input_storage
            )
        # END solution for eval_fully_async_apply

        paths = [input_storage.get_path(dep) for dep in eval_state.columns]

        return self.scope.expression_table(
            engine_input_table,
            paths,
            expressions,
            eval_state.deterministic or input_storage.append_only,
        )