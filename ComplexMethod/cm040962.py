def create(
        self,
        request: ResourceRequest[DynamoDBTableProperties],
    ) -> ProgressEvent[DynamoDBTableProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/TableName

        Required properties:
          - KeySchema

        Create-only properties:
          - /properties/TableName
          - /properties/ImportSourceSpecification

        Read-only properties:
          - /properties/Arn
          - /properties/StreamArn

        IAM permissions required:
          - dynamodb:CreateTable
          - dynamodb:DescribeImport
          - dynamodb:DescribeTable
          - dynamodb:DescribeTimeToLive
          - dynamodb:UpdateTimeToLive
          - dynamodb:UpdateContributorInsights
          - dynamodb:UpdateContinuousBackups
          - dynamodb:DescribeContinuousBackups
          - dynamodb:DescribeContributorInsights
          - dynamodb:EnableKinesisStreamingDestination
          - dynamodb:DisableKinesisStreamingDestination
          - dynamodb:DescribeKinesisStreamingDestination
          - dynamodb:ImportTable
          - dynamodb:ListTagsOfResource
          - dynamodb:TagResource
          - dynamodb:UpdateTable
          - kinesis:DescribeStream
          - kinesis:PutRecords
          - iam:CreateServiceLinkedRole
          - kms:CreateGrant
          - kms:Decrypt
          - kms:Describe*
          - kms:Encrypt
          - kms:Get*
          - kms:List*
          - kms:RevokeGrant
          - logs:CreateLogGroup
          - logs:CreateLogStream
          - logs:DescribeLogGroups
          - logs:DescribeLogStreams
          - logs:PutLogEvents
          - logs:PutRetentionPolicy
          - s3:GetObject
          - s3:GetObjectMetadata
          - s3:ListBucket

        """
        model = request.desired_state

        if not request.custom_context.get(REPEATED_INVOCATION):
            request.custom_context[REPEATED_INVOCATION] = True

            if not model.get("TableName"):
                model["TableName"] = util.generate_default_name(
                    request.stack_name, request.logical_resource_id
                )

            if model.get("ProvisionedThroughput"):
                model["ProvisionedThroughput"] = self.get_ddb_provisioned_throughput(model)

            if model.get("GlobalSecondaryIndexes"):
                model["GlobalSecondaryIndexes"] = self.get_ddb_global_sec_indexes(model)

            properties = [
                "TableName",
                "AttributeDefinitions",
                "KeySchema",
                "BillingMode",
                "ProvisionedThroughput",
                "LocalSecondaryIndexes",
                "GlobalSecondaryIndexes",
                "Tags",
                "SSESpecification",
            ]
            create_params = util.select_attributes(model, properties)

            if sse_specification := create_params.get("SSESpecification"):
                # rename bool attribute to fit boto call
                sse_specification["Enabled"] = sse_specification.pop("SSEEnabled")

            if stream_spec := model.get("StreamSpecification"):
                create_params["StreamSpecification"] = {
                    "StreamEnabled": True,
                    **(stream_spec or {}),
                }

            response = request.aws_client_factory.dynamodb.create_table(**create_params)
            model["Arn"] = response["TableDescription"]["TableArn"]

            if model.get("KinesisStreamSpecification"):
                request.aws_client_factory.dynamodb.enable_kinesis_streaming_destination(
                    **self.get_ddb_kinesis_stream_specification(model)
                )

            # add TTL config
            if ttl_config := model.get("TimeToLiveSpecification"):
                request.aws_client_factory.dynamodb.update_time_to_live(
                    TableName=model["TableName"], TimeToLiveSpecification=ttl_config
                )

            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        description = request.aws_client_factory.dynamodb.describe_table(
            TableName=model["TableName"]
        )

        if description["Table"]["TableStatus"] != "ACTIVE":
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        if model.get("TimeToLiveSpecification"):
            request.aws_client_factory.dynamodb.update_time_to_live(
                TableName=model["TableName"],
                TimeToLiveSpecification=model["TimeToLiveSpecification"],
            )

        if description["Table"].get("LatestStreamArn"):
            model["StreamArn"] = description["Table"]["LatestStreamArn"]

        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model=model,
        )