def calculate_alarm_state(alarm_arn: str) -> None:
    """
    Calculates and updates the state of the alarm

    :param alarm_arn: the arn of the alarm to be evaluated
    """
    alarm_details = get_metric_alarm_details_for_alarm_arn(alarm_arn)
    if not alarm_details:
        LOG.warning("Could not find alarm %s", alarm_arn)
        return

    client = get_cloudwatch_client_for_region_of_alarm(alarm_arn)

    query_date = datetime.utcnow().strftime(format="%Y-%m-%dT%H:%M:%S+0000")
    metric_values = collect_metric_data(alarm_details, client)

    state_reason_data = {
        "version": "1.0",
        "queryDate": query_date,
        "period": alarm_details["Period"],
        "recentDatapoints": [v for v in metric_values if v is not None],
        "threshold": alarm_details["Threshold"],
    }
    if alarm_details.get("Statistic"):
        state_reason_data["statistic"] = alarm_details["Statistic"]
    if alarm_details.get("Unit"):
        state_reason_data["unit"] = alarm_details["Unit"]

    alarm_name = alarm_details["AlarmName"]
    alarm_state = alarm_details["StateValue"]
    treat_missing_data = alarm_details.get("TreatMissingData", "missing")

    empty_datapoints = metric_values.count(None)
    if empty_datapoints == len(metric_values):
        evaluation_periods = alarm_details["EvaluationPeriods"]
        details_msg = (
            f"no datapoints were received for {evaluation_periods} period{'s' if evaluation_periods > 1 else ''} and "
            f"{evaluation_periods} missing datapoint{'s were' if evaluation_periods > 1 else ' was'} treated as"
        )
        if treat_missing_data == "missing":
            update_alarm_state(
                client,
                alarm_name,
                alarm_state,
                StateValue.INSUFFICIENT_DATA,
                f"{INSUFFICIENT_DATA}: {details_msg} [{treat_missing_data.capitalize()}].",
                state_reason_data=state_reason_data,
            )
        elif treat_missing_data == "breaching":
            update_alarm_state(
                client,
                alarm_name,
                alarm_state,
                StateValue.ALARM,
                f"{THRESHOLD_CROSSED}: {details_msg} [{treat_missing_data.capitalize()}].",
                state_reason_data=state_reason_data,
            )
        elif treat_missing_data == "notBreaching":
            update_alarm_state(
                client,
                alarm_name,
                alarm_state,
                StateValue.OK,
                f"{THRESHOLD_CROSSED}: {details_msg} [NonBreaching].",
                state_reason_data=state_reason_data,
            )
        # 'ignore': keep the same state
        return

    if is_triggering_premature_alarm(metric_values, alarm_details):
        if treat_missing_data == "missing":
            update_alarm_state(
                client,
                alarm_name,
                alarm_state,
                StateValue.ALARM,
                f"{THRESHOLD_CROSSED}: premature alarm for missing datapoints",
                state_reason_data=state_reason_data,
            )
        # for 'ignore' the state should be retained
        return

    # collect all non-empty datapoints from the evaluation interval
    collected_datapoints = [val for val in reversed(metric_values) if val is not None]

    # adding empty data points until amount of data points == "evaluation periods"
    evaluation_periods = alarm_details["EvaluationPeriods"]
    while len(collected_datapoints) < evaluation_periods and treat_missing_data in (
        "breaching",
        "notBreaching",
    ):
        # breaching/non-breaching datapoints will be evaluated
        # ignore/missing are not relevant
        collected_datapoints.append(None)

    if is_threshold_exceeded(collected_datapoints, alarm_details):
        update_alarm_state(
            client,
            alarm_name,
            alarm_state,
            StateValue.ALARM,
            THRESHOLD_CROSSED,
            state_reason_data=state_reason_data,
        )
    else:
        update_alarm_state(
            client,
            alarm_name,
            alarm_state,
            StateValue.OK,
            # TODO: cannot find a snapshot with StateValue.OK and the Threshold crossed value, verify this case
            THRESHOLD_CROSSED,
            state_reason_data=state_reason_data,
        )