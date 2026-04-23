def transform_query(params: dict[str, Any]) -> EiaPetroleumStatusReportQueryParams:
        """Transform the query parameters."""
        # pylint: disable=import-outside-toplevel
        from warnings import warn

        category = params.get("category", "balance_sheet")
        tables = WpsrTableMap.get(category, {})
        _table = params.get("table", "")

        if not _table:
            _table = "stocks" if category == "weekly_estimates" else "all"

        _tables = _table.split(",")

        if len(_tables) == 1 and _tables[0] == "all" and category == "weekly_estimates":
            raise OpenBBError(
                ValueError(
                    f"'all' is not a supported choice for {category}. Please choose from: {list(tables)}"
                )
            )

        if "all" in _tables and len(_tables) > 1:
            _tables.remove("all")
            warn("'all' cannot be used with other table choices. Ignoring 'all'.")

        for table in _tables:
            if table != "all" and table not in tables:
                raise OpenBBError(
                    ValueError(
                        f"Invalid table choice: {table}. Valid choices for {category}: {list(tables)}"
                    )
                )

        params["table"] = ",".join(_tables)

        return EiaPetroleumStatusReportQueryParams(**params)