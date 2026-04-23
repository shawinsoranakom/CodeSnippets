def create_table(
        self,
        context: RequestContext,
        create_table_input: CreateTableInput,
    ) -> CreateTableOutput:
        table_name = create_table_input["TableName"]

        # Return this specific error message to keep parity with AWS
        if self.table_exists(context.account_id, context.region, table_name):
            raise ResourceInUseException(f"Table already exists: {table_name}")

        billing_mode = create_table_input.get("BillingMode")
        provisioned_throughput = create_table_input.get("ProvisionedThroughput")
        if billing_mode == BillingMode.PAY_PER_REQUEST and provisioned_throughput is not None:
            raise ValidationException(
                "One or more parameter values were invalid: Neither ReadCapacityUnits nor WriteCapacityUnits can be "
                "specified when BillingMode is PAY_PER_REQUEST"
            )

        result = self.forward_request(context)

        table_description = result["TableDescription"]
        table_description["TableArn"] = table_arn = self.fix_table_arn(
            context.account_id, context.region, table_description["TableArn"]
        )

        backend = get_store(context.account_id, context.region)
        backend.table_definitions[table_name] = table_definitions = dict(create_table_input)
        backend.TABLE_REGION[table_name] = context.region

        if "TableId" not in table_definitions:
            table_definitions["TableId"] = long_uid()

        if "SSESpecification" in table_definitions:
            sse_specification = table_definitions.pop("SSESpecification")
            table_definitions["SSEDescription"] = SSEUtils.get_sse_description(
                context.account_id, context.region, sse_specification
            )

        if table_definitions:
            table_content = result.get("Table", {})
            table_content.update(table_definitions)
            table_description.update(table_content)

        if "TableClass" in table_definitions:
            table_class = table_description.pop("TableClass", None) or table_definitions.pop(
                "TableClass"
            )
            table_description["TableClassSummary"] = {"TableClass": table_class}

        if "GlobalSecondaryIndexes" in table_description:
            gsis = copy.deepcopy(table_description["GlobalSecondaryIndexes"])
            # update the different values, as DynamoDB-local v2 has a regression around GSI and does not return anything
            # anymore
            for gsi in gsis:
                index_name = gsi.get("IndexName", "")
                gsi.update(
                    {
                        "IndexArn": f"{table_arn}/index/{index_name}",
                        "IndexSizeBytes": 0,
                        "IndexStatus": "ACTIVE",
                        "ItemCount": 0,
                    }
                )
                gsi_provisioned_throughput = gsi.setdefault("ProvisionedThroughput", {})
                gsi_provisioned_throughput["NumberOfDecreasesToday"] = 0

                if billing_mode == BillingMode.PAY_PER_REQUEST:
                    gsi_provisioned_throughput["ReadCapacityUnits"] = 0
                    gsi_provisioned_throughput["WriteCapacityUnits"] = 0

            # table_definitions["GlobalSecondaryIndexes"] = gsis
            table_description["GlobalSecondaryIndexes"] = gsis

        if "ProvisionedThroughput" in table_description:
            if "NumberOfDecreasesToday" not in table_description["ProvisionedThroughput"]:
                table_description["ProvisionedThroughput"]["NumberOfDecreasesToday"] = 0

        if "WarmThroughput" in table_description:
            table_description["WarmThroughput"]["Status"] = "UPDATING"

        tags = table_definitions.pop("Tags", [])
        if tags:
            get_store(context.account_id, context.region).TABLE_TAGS[table_arn] = {
                tag["Key"]: tag["Value"] for tag in tags
            }

        # remove invalid attributes from result
        table_description.pop("Tags", None)
        table_description.pop("BillingMode", None)

        return result