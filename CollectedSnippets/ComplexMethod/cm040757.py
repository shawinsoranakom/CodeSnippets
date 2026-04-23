def describe_alarms_for_metric(
        self,
        context: RequestContext,
        metric_name: MetricName,
        namespace: Namespace,
        statistic: Statistic = None,
        extended_statistic: ExtendedStatistic = None,
        dimensions: Dimensions = None,
        period: Period = None,
        unit: StandardUnit = None,
        **kwargs,
    ) -> DescribeAlarmsForMetricOutput:
        store = self.get_store(context.account_id, context.region)
        alarms = [
            a.alarm
            for a in store.alarms.values()
            if isinstance(a, LocalStackMetricAlarm)
            and a.alarm.get("MetricName") == metric_name
            and a.alarm.get("Namespace") == namespace
        ]

        if statistic:
            alarms = [a for a in alarms if a.get("Statistic") == statistic]
        if dimensions:
            alarms = [a for a in alarms if a.get("Dimensions") == dimensions]
        if period:
            alarms = [a for a in alarms if a.get("Period") == period]
        if unit:
            alarms = [a for a in alarms if a.get("Unit") == unit]
        return DescribeAlarmsForMetricOutput(MetricAlarms=alarms)