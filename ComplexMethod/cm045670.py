def __call__(self, **kwargs):
        input = as_arg_tuple(kwargs)

        input_copy = ArgTuple.empty()
        iterated_with_universe_copy = ArgTuple.empty()

        # unwrap input and materialize input copy
        for name, arg in input.items():
            if isinstance(arg, pw.Table):
                input_copy[name] = self._copy_input_table(name, arg, unique=False)
            elif isinstance(arg, iterate_universe):
                iterated_with_universe_copy[name] = self._copy_input_table(
                    name, arg.table, unique=True
                )
                input[name] = arg.table
            else:
                raise TypeError(f"{name} has to be a Table instead of {type(arg)}")

        assert all(isinstance(table, pw.Table) for table in input)

        # call iteration logic with copied input and sort result by input order
        raw_result = self.func_spec.func(**input_copy, **iterated_with_universe_copy)
        arg_tuple = as_arg_tuple(raw_result)
        result = arg_tuple.process_input(input)
        if not iterated_with_universe_copy.is_key_subset_of(result):
            raise ValueError(
                "not all arguments marked as iterated returned from iteration"
            )
        for name, table in result.items():
            input_table: pw.Table = input[name]
            assert isinstance(table, pw.Table)
            input_schema = input_table.schema._dtypes()
            result_schema = table.schema._dtypes()
            if input_schema != result_schema:
                raise ValueError(
                    f"output: {result_schema}  of the iterated function does not correspond to the input: {input_schema}"  # noqa
                )
            table._sort_columns_by_other(input_table)

        # designate iterated arguments
        self.iterated_with_universe = input.intersect_keys(iterated_with_universe_copy)
        self.iterated = input.intersect_keys(result).subtract_keys(
            iterated_with_universe_copy
        )
        self.extra = input.subtract_keys(result)

        # do the same for proxied arguments
        self.iterated_with_universe_copy = iterated_with_universe_copy
        self.iterated_copy = input_copy.intersect_keys(result).subtract_keys(
            iterated_with_universe_copy
        )
        self.extra_copy = input_copy.subtract_keys(self.iterated_copy)

        # prepare iteration result
        self.result_iterated_with_universe = result.intersect_keys(
            iterated_with_universe_copy
        )
        self.result_iterated = result.subtract_keys(iterated_with_universe_copy)

        # materialize output
        output = type(arg_tuple).empty()
        for name, table in result.items():
            if name in self.iterated_with_universe_copy:
                universe = Universe()
            elif table._universe == input_copy[name]._universe:
                universe = input[name]._universe
            else:
                raise ValueError(
                    "iterated table not marked as 'iterate_universe' changed its universe"
                )
            output[name] = table._materialize(universe)
        output = output.with_same_order(
            self.result_iterated + self.result_iterated_with_universe
        )

        self._prepare_inputs(input)
        self._prepare_outputs(output)
        return output.to_output()