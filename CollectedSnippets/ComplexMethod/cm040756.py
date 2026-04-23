def describe_alarms(
        self,
        context: RequestContext,
        alarm_names: AlarmNames = None,
        alarm_name_prefix: AlarmNamePrefix = None,
        alarm_types: AlarmTypes = None,
        children_of_alarm_name: AlarmName = None,
        parents_of_alarm_name: AlarmName = None,
        state_value: StateValue = None,
        action_prefix: ActionPrefix = None,
        max_records: MaxRecords = None,
        next_token: NextToken = None,
        **kwargs,
    ) -> DescribeAlarmsOutput:
        store = self.get_store(context.account_id, context.region)
        alarms = list(store.alarms.values())
        if action_prefix:
            alarms = [a.alarm for a in alarms if a.alarm["AlarmAction"].startswith(action_prefix)]
        elif alarm_name_prefix:
            alarms = [a.alarm for a in alarms if a.alarm["AlarmName"].startswith(alarm_name_prefix)]
        elif alarm_names:
            alarms = [a.alarm for a in alarms if a.alarm["AlarmName"] in alarm_names]
        elif state_value:
            alarms = [a.alarm for a in alarms if a.alarm["StateValue"] == state_value]
        else:
            alarms = [a.alarm for a in list(store.alarms.values())]

        # TODO: Pagination
        metric_alarms = [a for a in alarms if a.get("AlarmRule") is None]
        composite_alarms = [a for a in alarms if a.get("AlarmRule") is not None]
        return DescribeAlarmsOutput(CompositeAlarms=composite_alarms, MetricAlarms=metric_alarms)