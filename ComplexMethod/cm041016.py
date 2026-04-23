def create_flow_logs(
        self,
        context: RequestContext,
        request: CreateFlowLogsRequest,
        **kwargs,
    ) -> CreateFlowLogsResult:
        if request.get("LogDestination") and request.get("LogGroupName"):
            raise CommonServiceException(
                code="InvalidParameter",
                message="Please only provide LogGroupName or only provide LogDestination.",
            )
        if request.get("LogDestinationType") == "s3":
            if request.get("LogGroupName"):
                raise CommonServiceException(
                    code="InvalidParameter",
                    message="LogDestination type must be cloud-watch-logs if LogGroupName is provided.",
                )
            elif not (bucket_arn := request.get("LogDestination")):
                raise CommonServiceException(
                    code="InvalidParameter",
                    message="LogDestination can't be empty if LogGroupName is not provided.",
                )

            # Moto will check in memory whether the bucket exists in Moto itself
            # we modify the request to not send a destination, so that the validation does not happen
            # we can add the validation ourselves
            service_request = copy.deepcopy(request)
            service_request["LogDestinationType"] = "__placeholder__"
            bucket_name = bucket_arn.split(":", 5)[5].split("/")[0]
            # TODO: validate how IAM is enforced? probably with DeliverLogsPermissionArn
            s3_client = connect_to().s3
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except Exception as e:
                LOG.debug(
                    "An exception occurred when trying to create FlowLogs with S3 destination: %s",
                    e,
                )
                return CreateFlowLogsResult(
                    FlowLogIds=[],
                    Unsuccessful=[
                        UnsuccessfulItem(
                            Error=UnsuccessfulItemError(
                                Code="400",
                                Message=f"LogDestination: {bucket_name} does not exist",
                            ),
                            ResourceId=resource_id,
                        )
                        for resource_id in request.get("ResourceIds", [])
                    ],
                )

            response: CreateFlowLogsResult = call_moto_with_request(context, service_request)
            moto_backend = get_moto_backend(context)
            for flow_log_id in response["FlowLogIds"]:
                if flow_log := moto_backend.flow_logs.get(flow_log_id):
                    # just to be sure to not override another value, we only replace if it's the placeholder
                    flow_log.log_destination_type = flow_log.log_destination_type.replace(
                        "__placeholder__", "s3"
                    )
        else:
            response = call_moto(context)

        return response