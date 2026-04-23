def create(
        self,
        request: ResourceRequest[DynamoDBGlobalTableProperties],
    ) -> ProgressEvent[DynamoDBGlobalTableProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/TableName

        Required properties:
          - KeySchema
          - AttributeDefinitions
          - Replicas

        Create-only properties:
          - /properties/LocalSecondaryIndexes
          - /properties/TableName
          - /properties/KeySchema

        Read-only properties:
          - /properties/Arn
          - /properties/StreamArn
          - /properties/TableId

        IAM permissions required:
          - dynamodb:CreateTable
          - dynamodb:CreateTableReplica
          - dynamodb:Describe*
          - dynamodb:UpdateTimeToLive
          - dynamodb:UpdateContributorInsights
          - dynamodb:UpdateContinuousBackups
          - dynamodb:ListTagsOfResource
          - dynamodb:Query
          - dynamodb:Scan
          - dynamodb:UpdateItem
          - dynamodb:PutItem
          - dynamodb:GetItem
          - dynamodb:DeleteItem
          - dynamodb:BatchWriteItem
          - dynamodb:TagResource
          - dynamodb:EnableKinesisStreamingDestination
          - dynamodb:DisableKinesisStreamingDestination
          - dynamodb:DescribeKinesisStreamingDestination
          - dynamodb:DescribeTableReplicaAutoScaling
          - dynamodb:UpdateTableReplicaAutoScaling
          - dynamodb:TagResource
          - application-autoscaling:DeleteScalingPolicy
          - application-autoscaling:DeleteScheduledAction
          - application-autoscaling:DeregisterScalableTarget
          - application-autoscaling:Describe*
          - application-autoscaling:PutScalingPolicy
          - application-autoscaling:PutScheduledAction
          - application-autoscaling:RegisterScalableTarget
          - kinesis:ListStreams
          - kinesis:DescribeStream
          - kinesis:PutRecords
          - kms:CreateGrant
          - kms:Describe*
          - kms:Get*
          - kms:List*
          - kms:RevokeGrant
          - cloudwatch:PutMetricData

        """
        model = request.desired_state

        if not request.custom_context.get(REPEATED_INVOCATION):
            request.custom_context[REPEATED_INVOCATION] = True

            if not model.get("TableName"):
                model["TableName"] = util.generate_default_name(
                    stack_name=request.stack_name, logical_resource_id=request.logical_resource_id
                )

            create_params = util.select_attributes(
                model,
                [
                    "AttributeDefinitions",
                    "BillingMode",
                    "GlobalSecondaryIndexes",
                    "KeySchema",
                    "LocalSecondaryIndexes",
                    "Replicas",
                    "SSESpecification",
                    "StreamSpecification",
                    "TableName",
                    "WriteProvisionedThroughputSettings",
                ],
            )

            replicas = create_params.pop("Replicas", [])

            if sse_specification := create_params.get("SSESpecification"):
                # rename bool attribute to fit boto call
                sse_specification["Enabled"] = sse_specification.pop("SSEEnabled")

            if stream_spec := model.get("StreamSpecification"):
                create_params["StreamSpecification"] = {
                    "StreamEnabled": True,
                    **stream_spec,
                }

            creation_response = request.aws_client_factory.dynamodb.create_table(**create_params)
            model["Arn"] = creation_response["TableDescription"]["TableArn"]
            model["TableId"] = creation_response["TableDescription"]["TableId"]

            if creation_response["TableDescription"].get("LatestStreamArn"):
                model["StreamArn"] = creation_response["TableDescription"]["LatestStreamArn"]

            replicas_to_create = []
            for replica in replicas:
                create = {
                    "RegionName": replica.get("Region"),
                    "KMSMasterKeyId": replica.get("KMSMasterKeyId"),
                    "ProvisionedThroughputOverride": replica.get("ProvisionedThroughputOverride"),
                    "GlobalSecondaryIndexes": replica.get("GlobalSecondaryIndexes"),
                    "TableClassOverride": replica.get("TableClassOverride"),
                }

                create = {k: v for k, v in create.items() if v is not None}

                replicas_to_create.append({"Create": create})

                request.aws_client_factory.dynamodb.update_table(
                    ReplicaUpdates=replicas_to_create, TableName=model["TableName"]
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

        status = request.aws_client_factory.dynamodb.describe_table(TableName=model["TableName"])[
            "Table"
        ]["TableStatus"]
        if status == "ACTIVE":
            return ProgressEvent(
                status=OperationStatus.SUCCESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        elif status == "CREATING":
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )
        else:
            return ProgressEvent(
                status=OperationStatus.FAILED,
                resource_model=model,
                custom_context=request.custom_context,
                message=f"Table creation failed with status {status}",
            )