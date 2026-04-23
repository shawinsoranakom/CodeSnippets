def _handle_query_submit(self, data, event_type, label):
        import pandas as pd
        from pywry.grid import build_column_defs, normalize_data

        query_str = self._pending_query or ""
        if not query_str.strip():
            return

        lowered = query_str.lower()
        for token in self._BLOCKED_TOKENS:
            if token in lowered:
                self._app.emit(
                    "pywry:alert",
                    {"message": f"Blocked token: '{token}'", "type": "error"},
                    label,
                )
                return

        try:
            result = eval(  # noqa: S307  # pylint: disable=W0123
                query_str,
                {"__builtins__": {}},
                {"df": self._original_df, "pd": pd},
            )
            if not isinstance(result, pd.DataFrame):
                self._app.emit(
                    "pywry:alert",
                    {"message": "Expression must return a DataFrame", "type": "error"},
                    label,
                )
                return
            include_named_index = any(name is not None for name in result.index.names)
            result_for_grid = result.reset_index() if include_named_index else result
            grid_data = normalize_data(result_for_grid)
            col_defs = build_column_defs(
                columns=grid_data.columns,
                index_columns=grid_data.index_columns,
                column_types=grid_data.column_types,
            )
            self._app.emit(
                "grid:update-columns",
                {"columnDefs": col_defs},
                label,
            )
            self._app.emit(
                "grid:update-data",
                {"data": grid_data.row_data, "strategy": "set"},
                label,
            )
        except Exception as exc:
            self._app.emit(
                "pywry:alert",
                {"message": f"Query error: {exc}", "type": "error"},
                label,
            )