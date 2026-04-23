def transform_query(params: dict[str, Any]) -> CboeIndexHistoricalQueryParams:
        """Transform the query."""
        # pylint: disable=import-outside-toplevel
        from datetime import timedelta

        transformed_params = params.copy()
        now = datetime.now()
        if (
            len(params.get("symbol", "").split(",")) > 1
            and params.get("start_date") is None
        ):
            transformed_params["start_date"] = (
                transformed_params["start_date"]
                if transformed_params["start_date"]
                else (now - timedelta(days=720)).strftime("%Y-%m-%d")
            )
        if transformed_params.get("start_date") is None:
            transformed_params["start_date"] = (
                transformed_params["start_date"]
                if transformed_params.get("start_date")
                else "1950-01-01"
            )
        if params.get("end_date") is None:
            transformed_params["end_date"] = (
                transformed_params["end_date"]
                if transformed_params.get("end_date")
                else now.strftime("%Y-%m-%d")
            )

        return CboeIndexHistoricalQueryParams(**transformed_params)