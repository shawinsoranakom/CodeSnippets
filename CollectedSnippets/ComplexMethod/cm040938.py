def describe_table(
        self, context: RequestContext, table_name: TableName, **kwargs
    ) -> DescribeTableOutput:
        global_table_region = self.get_global_table_region(context, table_name)

        result = self._forward_request(context=context, region=global_table_region)
        table_description: TableDescription = result["Table"]

        # Update table properties from LocalStack stores
        if table_props := get_store(context.account_id, context.region).table_properties.get(
            table_name
        ):
            table_description.update(table_props)

        store = get_store(context.account_id, context.region)

        # Update replication details
        replicas: dict[RegionName, ReplicaDescription] = store.REPLICAS.get(table_name, {})

        replica_description_list = []

        if global_table_region != context.region:
            replica_description_list.append(
                ReplicaDescription(
                    RegionName=global_table_region, ReplicaStatus=ReplicaStatus.ACTIVE
                )
            )

        for replica_region, replica_description in replicas.items():
            # The replica in the region being queried must not be returned
            if replica_region != context.region:
                replica_description_list.append(replica_description)

        if replica_description_list:
            table_description.update({"Replicas": replica_description_list})

        # update only TableId and SSEDescription if present
        if table_definitions := store.table_definitions.get(table_name):
            for key in ["TableId", "SSEDescription"]:
                if table_definitions.get(key):
                    table_description[key] = table_definitions[key]
            if "TableClass" in table_definitions:
                table_description["TableClassSummary"] = {
                    "TableClass": table_definitions["TableClass"]
                }
            if warm_throughput := table_definitions.get("WarmThroughput"):
                table_description["WarmThroughput"] = warm_throughput.copy()
                table_description["WarmThroughput"].setdefault("Status", "ACTIVE")

        if "GlobalSecondaryIndexes" in table_description:
            for gsi in table_description["GlobalSecondaryIndexes"]:
                default_values = {
                    "NumberOfDecreasesToday": 0,
                    "ReadCapacityUnits": 0,
                    "WriteCapacityUnits": 0,
                }
                # even if the billing mode is PAY_PER_REQUEST, AWS returns the Read and Write Capacity Units
                # Terraform depends on this parity for update operations
                gsi["ProvisionedThroughput"] = default_values | gsi.get("ProvisionedThroughput", {})

        # Set defaults for warm throughput
        if "WarmThroughput" not in table_description:
            billing_mode = table_definitions.get("BillingMode") if table_definitions else None
            table_description["WarmThroughput"] = {
                "ReadUnitsPerSecond": 12000 if billing_mode == "PAY_PER_REQUEST" else 5,
                "WriteUnitsPerSecond": 4000 if billing_mode == "PAY_PER_REQUEST" else 5,
            }
        table_description["WarmThroughput"]["Status"] = (
            table_description.get("TableStatus") or "ACTIVE"
        )

        return DescribeTableOutput(
            Table=select_from_typed_dict(TableDescription, table_description)
        )