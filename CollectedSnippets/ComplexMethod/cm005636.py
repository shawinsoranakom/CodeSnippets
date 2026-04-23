def __call__(self, table=None, query=None, **kwargs):
        # Returns tqa_pipeline_inputs of shape:
        # [
        #   {"table": pd.DataFrame, "query": list[str]},
        #   ...,
        #   {"table": pd.DataFrame, "query" : list[str]}
        # ]
        requires_backends(self, "pandas")
        import pandas as pd

        if table is None:
            raise ValueError("Keyword argument `table` cannot be None.")
        elif query is None:
            if isinstance(table, dict) and table.get("query") is not None and table.get("table") is not None:
                tqa_pipeline_inputs = [table]
            elif isinstance(table, list) and len(table) > 0:
                if not all(isinstance(d, dict) for d in table):
                    raise ValueError(
                        f"Keyword argument `table` should be a list of dict, but is {(type(d) for d in table)}"
                    )

                if table[0].get("query") is not None and table[0].get("table") is not None:
                    tqa_pipeline_inputs = table
                else:
                    raise ValueError(
                        "If keyword argument `table` is a list of dictionaries, each dictionary should have a `table`"
                        f" and `query` key, but only dictionary has keys {table[0].keys()} `table` and `query` keys."
                    )
            elif Dataset is not None and isinstance(table, Dataset) or isinstance(table, types.GeneratorType):
                return table
            else:
                raise ValueError(
                    "Invalid input. Keyword argument `table` should be either of type `dict` or `list`, but "
                    f"is {type(table)})"
                )
        else:
            tqa_pipeline_inputs = [{"table": table, "query": query}]

        for tqa_pipeline_input in tqa_pipeline_inputs:
            if not isinstance(tqa_pipeline_input["table"], pd.DataFrame):
                if tqa_pipeline_input["table"] is None:
                    raise ValueError("Table cannot be None.")

                tqa_pipeline_input["table"] = pd.DataFrame(tqa_pipeline_input["table"])

        return tqa_pipeline_inputs