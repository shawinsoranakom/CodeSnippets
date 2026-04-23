def describe_alarm_history(
        self,
        context: RequestContext,
        alarm_name: AlarmName | None = None,
        alarm_contributor_id: ContributorId | None = None,
        alarm_types: AlarmTypes | None = None,
        history_item_type: HistoryItemType | None = None,
        start_date: Timestamp | None = None,
        end_date: Timestamp | None = None,
        max_records: MaxRecords | None = None,
        next_token: NextToken | None = None,
        scan_by: ScanBy | None = None,
        **kwargs,
    ) -> DescribeAlarmHistoryOutput:
        store = self.get_store(context.account_id, context.region)
        history = store.histories
        if alarm_name:
            history = [h for h in history if h["AlarmName"] == alarm_name]

        if start_date:
            history = [h for h in history if (date := h.get("Timestamp")) and date >= start_date]
        if end_date:
            history = [h for h in history if (date := h.get("Timestamp")) and date <= end_date]
        return DescribeAlarmHistoryOutput(AlarmHistoryItems=history)