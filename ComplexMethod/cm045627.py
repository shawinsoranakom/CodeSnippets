def table_from_pandas(
        self,
        df: pd.DataFrame,
        id_from: list[str] | None = None,
        unsafe_trusted_ids: bool = False,
        schema: type[Schema] | None = None,
        _stacklevel: int = 1,
    ) -> Table:
        """A function for creating a table from a pandas DataFrame. If the DataFrame
        contains a column ``_time``, rows will be split into batches with timestamps from ``_time`` column.
        Then ``_worker`` column will be interpreted as the id of a worker which will process the row and
        ``_diff`` column as an event type with ``1`` treated as inserting row and ``-1`` as removing.
        """
        if schema is None:
            schema = schema_from_pandas(
                df, exclude_columns={"_time", "_diff", "_worker"}
            )
        schema, api_schema = read_schema(schema)
        value_fields: list[api.ValueField] = api_schema["value_fields"]

        if "_time" not in df:
            df["_time"] = [2] * len(df)
        if "_worker" not in df:
            df["_worker"] = [0] * len(df)
        if "_diff" not in df:
            df["_diff"] = [1] * len(df)

        batches: dict[
            int, dict[int, list[tuple[int, api.Pointer, list[api.Value]]]]
        ] = {}

        ids = api.ids_from_pandas(
            df, api.ConnectorProperties(unsafe_trusted_ids=unsafe_trusted_ids), id_from
        )

        for row_index in range(len(df)):
            row = df.iloc[row_index]
            time = row["_time"]
            key = ids[df.index[row_index]]
            worker = row["_worker"]

            if time not in batches:
                batches[time] = {}

            if worker not in batches[time]:
                batches[time][worker] = []

            values = []
            for value_field in value_fields:
                column = value_field.name
                value = api.denumpify(row[column])
                values.append(value)
            diff = row["_diff"]

            batches[time][worker].append((diff, key, values))

        return self._table_from_dict(batches, schema, _stacklevel=_stacklevel + 1)