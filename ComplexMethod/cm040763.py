def create_message_response_update_state_sns(alarm, old_state):
    response = {
        "AWSAccountId": extract_account_id_from_arn(alarm.alarm_arn),
        "OldStateValue": old_state,
        "AlarmName": alarm.name,
        "AlarmDescription": alarm.description or "",
        "AlarmConfigurationUpdatedTimestamp": _to_iso_8601_datetime_with_nanoseconds(
            alarm.configuration_updated_timestamp
        ),
        "NewStateValue": alarm.state_value,
        "NewStateReason": alarm.state_reason,
        "StateChangeTime": _to_iso_8601_datetime_with_nanoseconds(alarm.state_updated_timestamp),
        # the long-name for 'region' should be used - as we don't have it, we use the short name
        # which needs to be slightly changed to make snapshot tests work
        "Region": alarm.region_name.replace("-", " ").capitalize(),
        "AlarmArn": alarm.alarm_arn,
        "OKActions": alarm.ok_actions or [],
        "AlarmActions": alarm.alarm_actions or [],
        "InsufficientDataActions": alarm.insufficient_data_actions or [],
    }

    # collect trigger details
    details = {
        "MetricName": alarm.metric_name or "",
        "Namespace": alarm.namespace or "",
        "Unit": alarm.unit or None,  # testing with AWS revealed this currently returns None
        "Period": int(alarm.period) if alarm.period else 0,
        "EvaluationPeriods": int(alarm.evaluation_periods) if alarm.evaluation_periods else 0,
        "ComparisonOperator": alarm.comparison_operator or "",
        "Threshold": float(alarm.threshold) if alarm.threshold else 0.0,
        "TreatMissingData": alarm.treat_missing_data or "",
        "EvaluateLowSampleCountPercentile": alarm.evaluate_low_sample_count_percentile or "",
    }

    # Dimensions not serializable
    dimensions = []
    if alarm.dimensions:
        for d in alarm.dimensions:
            dimensions.append({"value": d.value, "name": d.name})

    details["Dimensions"] = dimensions or ""

    if alarm.statistic:
        details["StatisticType"] = "Statistic"
        details["Statistic"] = camel_to_snake_case(alarm.statistic).upper()  # AWS returns uppercase
    elif alarm.extended_statistic:
        details["StatisticType"] = "ExtendedStatistic"
        details["ExtendedStatistic"] = alarm.extended_statistic

    response["Trigger"] = details

    return json.dumps(response)