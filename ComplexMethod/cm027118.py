async def _async_handle_get_statistics_service(
    service: ServiceCall,
) -> ServiceResponse:
    """Handle calls to the get_statistics service."""
    hass = service.hass
    start_time = dt_util.as_utc(service.data["start_time"])
    end_time = (
        dt_util.as_utc(service.data["end_time"]) if "end_time" in service.data else None
    )

    statistic_ids = service.data["statistic_ids"]
    types = service.data["types"]
    period = service.data["period"]
    units = service.data.get("units")

    result = await hass.data[DATA_INSTANCE].async_add_executor_job(
        statistics_during_period,
        hass,
        start_time,
        end_time,
        statistic_ids,
        period,
        units,
        types,
    )

    formatted_result: JsonObjectType = {}
    for statistic_id, statistic_rows in result.items():
        formatted_statistic_rows: JsonArrayType = []

        for row in statistic_rows:
            formatted_row: JsonObjectType = {
                "start": dt_util.utc_from_timestamp(row["start"]).isoformat(),
                "end": dt_util.utc_from_timestamp(row["end"]).isoformat(),
            }
            if (last_reset := row.get("last_reset")) is not None:
                formatted_row["last_reset"] = dt_util.utc_from_timestamp(
                    last_reset
                ).isoformat()
            if (state := row.get("state")) is not None:
                formatted_row["state"] = state
            if (sum_value := row.get("sum")) is not None:
                formatted_row["sum"] = sum_value
            if (min_value := row.get("min")) is not None:
                formatted_row["min"] = min_value
            if (max_value := row.get("max")) is not None:
                formatted_row["max"] = max_value
            if (mean := row.get("mean")) is not None:
                formatted_row["mean"] = mean
            if (change := row.get("change")) is not None:
                formatted_row["change"] = change

            formatted_statistic_rows.append(formatted_row)

        formatted_result[statistic_id] = formatted_statistic_rows

    return {"statistics": formatted_result}