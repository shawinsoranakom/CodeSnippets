def transform_query(params: dict[str, Any]) -> IntrinioMarketSnapshotsQueryParams:
        """Transform the query params."""
        # pylint: disable=import-outside-toplevel
        from pytz import timezone

        transformed_params = params

        if "date" in transformed_params:
            if isinstance(transformed_params["date"], datetime):
                dt = transformed_params["date"]
                dt = dt.astimezone(tz=timezone("America/New_York"))
            if isinstance(transformed_params["date"], dateType):
                dt = transformed_params["date"]  # type: ignore
                if isinstance(dt, dateType):
                    dt = datetime(
                        dt.year,
                        dt.month,
                        dt.day,
                        20,
                        0,
                        0,
                        0,
                        tzinfo=timezone("America/New_York"),
                    )
            if isinstance(transformed_params["date"], str):
                dt = datetime.fromisoformat(transformed_params["date"])
            else:
                try:
                    dt = datetime.fromisoformat(str(transformed_params["date"]))  # type: ignore
                except ValueError as exc:
                    raise OpenBBError(
                        "Invalid date format. Please use '2024-03-08T12:15-0400'."
                    ) from exc

            transformed_params["date"] = (
                dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
                .replace("+", "-")
                .replace("T00:", "T20:")
                if isinstance(dt, datetime)
                else dt
            )
        return IntrinioMarketSnapshotsQueryParams(**transformed_params)