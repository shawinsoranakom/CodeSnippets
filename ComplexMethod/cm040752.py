def _validate_parameters_for_put_metric_data(metric_data: MetricData) -> None:
    for index, metric_item in enumerate(metric_data):
        indexplusone = index + 1
        if metric_item.get("Value") and metric_item.get("Values"):
            raise InvalidParameterCombinationException(
                f"The parameters MetricData.member.{indexplusone}.Value and MetricData.member.{indexplusone}.Values are mutually exclusive and you have specified both."
            )

        if metric_item.get("StatisticValues") and metric_item.get("Value"):
            raise InvalidParameterCombinationException(
                f"The parameters MetricData.member.{indexplusone}.Value and MetricData.member.{indexplusone}.StatisticValues are mutually exclusive and you have specified both."
            )

        if metric_item.get("Values") and metric_item.get("Counts"):
            values = metric_item.get("Values")
            counts = metric_item.get("Counts")
            if len(values) != len(counts):
                raise InvalidParameterValueException(
                    f"The parameters MetricData.member.{indexplusone}.Values and MetricData.member.{indexplusone}.Counts must be of the same size."
                )