def put_metric_alarm(self, context: RequestContext, request: PutMetricAlarmInput) -> None:
        # missing will be the default, when not set (but it will not explicitly be set)
        if request.get("TreatMissingData", "missing") not in [
            "breaching",
            "notBreaching",
            "ignore",
            "missing",
        ]:
            raise ValidationException(
                f"The value {request['TreatMissingData']} is not supported for TreatMissingData parameter. Supported values are [breaching, notBreaching, ignore, missing]."
            )
            # do some sanity checks:
        if request.get("Period"):
            # Valid values are 10, 30, and any multiple of 60.
            value = request.get("Period")
            if value not in (10, 30):
                if value % 60 != 0:
                    raise ValidationException("Period must be 10, 30 or a multiple of 60")
        if request.get("Statistic"):
            if request.get("Statistic") not in [
                "SampleCount",
                "Average",
                "Sum",
                "Minimum",
                "Maximum",
            ]:
                raise ValidationException(
                    f"Value '{request.get('Statistic')}' at 'statistic' failed to satisfy constraint: Member must satisfy enum value set: [Maximum, SampleCount, Sum, Minimum, Average]"
                )

        extended_statistic = request.get("ExtendedStatistic")
        if extended_statistic and not extended_statistic.startswith("p"):
            raise InvalidParameterValueException(
                f"The value {extended_statistic} for parameter ExtendedStatistic is not supported."
            )
        evaluate_low_sample_count_percentile = request.get("EvaluateLowSampleCountPercentile")
        if evaluate_low_sample_count_percentile and evaluate_low_sample_count_percentile not in (
            "evaluate",
            "ignore",
        ):
            raise ValidationException(
                f"Option {evaluate_low_sample_count_percentile} is not supported. "
                "Supported options for parameter EvaluateLowSampleCountPercentile are evaluate and ignore."
            )
        with _STORE_LOCK:
            store = self.get_store(context.account_id, context.region)
            metric_alarm = LocalStackMetricAlarm(context.account_id, context.region, {**request})
            alarm_arn = metric_alarm.alarm["AlarmArn"]
            store.alarms[alarm_arn] = metric_alarm
            self.alarm_scheduler.schedule_metric_alarm(alarm_arn)
            self._set_resource_tags(
                alarm_arn, context.account_id, context.region, request.get("Tags", [])
            )