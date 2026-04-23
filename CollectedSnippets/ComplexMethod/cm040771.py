def put_log_events(
        self,
        context: RequestContext,
        log_group_name: LogGroupName,
        log_stream_name: LogStreamName,
        log_events: InputLogEvents,
        sequence_token: SequenceToken | None = None,
        entity: Entity | None = None,
        **kwargs,
    ) -> PutLogEventsResponse:
        logs_backend = get_moto_logs_backend(context.account_id, context.region)
        metric_filters = logs_backend.filters.metric_filters if is_api_enabled("cloudwatch") else []
        for metric_filter in metric_filters:
            pattern = metric_filter.get("filterPattern", "")
            transformations = metric_filter.get("metricTransformations", [])
            matches = get_pattern_matcher(pattern)
            for log_event in log_events:
                if matches(pattern, log_event):
                    for tf in transformations:
                        value = tf.get("metricValue") or "1"
                        if "$size" in value:
                            LOG.info(
                                "Expression not yet supported for log filter metricValue", value
                            )
                        value = float(value) if is_number(value) else 1
                        data = [{"MetricName": tf["metricName"], "Value": value}]
                        try:
                            client = connect_to(
                                aws_access_key_id=context.account_id, region_name=context.region
                            ).cloudwatch
                            client.put_metric_data(Namespace=tf["metricNamespace"], MetricData=data)
                        except Exception as e:
                            LOG.info(
                                "Unable to put metric data for matching CloudWatch log events", e
                            )
        return call_moto(context)