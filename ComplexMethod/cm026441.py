def validate(result: Any) -> list[Forecast] | None:
        if template_validators.check_result_for_none(result):
            return None

        if not isinstance(result, list):
            template_validators.log_validation_result_error(
                entity,
                option,
                result,
                f"expected a list, {weather_message}",
            )

        raised = False
        for forecast in result:
            if not isinstance(forecast, dict):
                raised = True
                template_validators.log_validation_result_error(
                    entity,
                    option,
                    result,
                    f"expected a list of forecast dictionaries, got {forecast}, {weather_message}",
                )
                continue

            diff_result = set().union(forecast.keys()).difference(CHECK_FORECAST_KEYS)
            if diff_result:
                raised = True
                template_validators.log_validation_result_error(
                    entity,
                    option,
                    result,
                    f"expected valid forecast keys, unallowed keys: ({diff_result}) for {forecast}, {weather_message}",
                )
            if forecast_type == "twice_daily" and "is_daytime" not in forecast:
                raised = True
                template_validators.log_validation_result_error(
                    entity,
                    option,
                    result,
                    f"`is_daytime` is missing in twice_daily forecast {forecast}, {weather_message}",
                )
            if "datetime" not in forecast:
                raised = True
                template_validators.log_validation_result_error(
                    entity,
                    option,
                    result,
                    f"`datetime` is missing in forecast, got {forecast}, {weather_message}",
                )

        if raised:
            return None

        return result