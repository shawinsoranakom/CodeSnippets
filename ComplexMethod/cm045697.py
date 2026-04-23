def _run(
        self,
        operator: InputOperator,
        output_storages: dict[Table, Storage],
    ):
        datasource = operator.datasource
        if self.graph_builder.debug and operator.debug_datasource is not None:
            if (
                datasource.schema._dtypes()
                != operator.debug_datasource.schema._dtypes()
            ):
                raise ValueError("wrong schema of debug data")
            for table in operator.output_tables:
                assert table.schema is not None
                materialized_table = api.static_table_from_pandas(
                    scope=self.scope,
                    df=operator.debug_datasource.data,
                    connector_properties=operator.debug_datasource.connector_properties,
                    schema=operator.debug_datasource.schema,
                )
                self.state.set_table(output_storages[table], materialized_table)
        elif isinstance(datasource, PandasDataSource):
            for table in operator.output_tables:
                assert table.schema is not None
                materialized_table = api.static_table_from_pandas(
                    scope=self.scope,
                    df=datasource.data,
                    connector_properties=datasource.connector_properties,
                    schema=datasource.schema,
                )
                self.state.set_table(output_storages[table], materialized_table)
        elif isinstance(datasource, GenericDataSource):
            for table in operator.output_tables:
                assert table.schema is not None
                materialized_table = self.scope.connector_table(
                    data_source=datasource.datastorage,
                    data_format=datasource.dataformat,
                    properties=datasource.connector_properties,
                )
                self.state.set_table(output_storages[table], materialized_table)
        elif isinstance(datasource, EmptyDataSource):
            for table in operator.output_tables:
                assert table.schema is not None
                materialized_table = self.scope.empty_table(
                    datasource.connector_properties
                )
                self.state.set_table(output_storages[table], materialized_table)
        elif isinstance(datasource, ImportDataSource):
            for table in operator.output_tables:
                assert table.schema is not None
                exported_table = datasource.callback(self.scope)
                materialized_table = self.scope.import_table(exported_table)
                self.state.set_table(output_storages[table], materialized_table)
        elif isinstance(datasource, ErrorLogDataSource):
            for table in operator.output_tables:
                (materialized_table, error_log) = self.scope.error_log(
                    properties=datasource.connector_properties
                )
                self.state.set_table(output_storages[table], materialized_table)
                self.state.set_error_log(table, error_log)
        else:
            raise RuntimeError("datasource not supported")