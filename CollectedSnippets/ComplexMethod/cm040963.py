def get_ddb_global_sec_indexes(
        self,
        properties: dict,
    ) -> list | None:
        args: list = properties.get("GlobalSecondaryIndexes")
        is_ondemand = properties.get("BillingMode") == "PAY_PER_REQUEST"
        if not args:
            return

        for index in args:
            # we ignore ContributorInsightsSpecification as not supported yet in DynamoDB and CloudWatch
            index.pop("ContributorInsightsSpecification", None)
            provisioned_throughput = index.get("ProvisionedThroughput")
            if is_ondemand and provisioned_throughput is None:
                pass  # optional for API calls
            elif provisioned_throughput is not None:
                # convert types
                if isinstance((read_units := provisioned_throughput["ReadCapacityUnits"]), str):
                    provisioned_throughput["ReadCapacityUnits"] = int(read_units)
                if isinstance((write_units := provisioned_throughput["WriteCapacityUnits"]), str):
                    provisioned_throughput["WriteCapacityUnits"] = int(write_units)
            else:
                raise Exception("Can't specify ProvisionedThroughput with PAY_PER_REQUEST")
        return args