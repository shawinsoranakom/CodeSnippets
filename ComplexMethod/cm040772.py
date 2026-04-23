def describe_log_groups(
        self, context: RequestContext, request: DescribeLogGroupsRequest
    ) -> DescribeLogGroupsResponse:
        region_backend = get_moto_logs_backend(context.account_id, context.region)

        prefix: str | None = request.get("logGroupNamePrefix", "")
        pattern: str | None = request.get("logGroupNamePattern", "")

        if pattern and prefix:
            raise InvalidParameterException(
                "LogGroup name prefix and LogGroup name pattern are mutually exclusive parameters."
            )

        moto_groups = copy.deepcopy(dict(region_backend.groups)).values()

        groups = [
            {"logGroupClass": LogGroupClass.STANDARD} | group.to_describe_dict()
            for group in sorted(moto_groups, key=lambda g: g.name)
            if not (prefix or pattern)
            or (prefix and group.name.startswith(prefix))
            or (pattern and pattern in group.name)
        ]

        return DescribeLogGroupsResponse(logGroups=groups)