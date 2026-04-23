def is_triggering_premature_alarm(metric_values: list[float], alarm_details: MetricAlarm) -> bool:
    """
    Checks if a premature alarm should be triggered.
    https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html#CloudWatch-alarms-avoiding-premature-transition:

    [...] alarms are designed to always go into ALARM state when the oldest available breaching datapoint during the Evaluation
    Periods number of data points is at least as old as the value of Datapoints to Alarm, and all other more recent data
    points are breaching or missing. In this case, the alarm goes into ALARM state even if the total number of datapoints
    available is lower than M (Datapoints to Alarm).
    This alarm logic applies to M out of N alarms as well.
    """
    treat_missing_data = alarm_details.get("TreatMissingData", "missing")
    if treat_missing_data not in ("missing", "ignore"):
        return False

    datapoints_to_alarm = alarm_details.get("DatapointsToAlarm", 1)
    if datapoints_to_alarm > 1:
        comparison_operator = alarm_details["ComparisonOperator"]
        threshold = alarm_details["Threshold"]
        oldest_datapoints = metric_values[:-datapoints_to_alarm]
        if oldest_datapoints.count(None) == len(oldest_datapoints):
            if metric_values[-datapoints_to_alarm] and COMPARISON_OPS.get(comparison_operator)(
                metric_values[-datapoints_to_alarm], threshold
            ):
                values = list(filter(None, metric_values[len(oldest_datapoints) :]))
                if all(
                    COMPARISON_OPS.get(comparison_operator)(value, threshold) for value in values
                ):
                    return True
    return False