def update_table(
        self, context: RequestContext, update_table_input: UpdateTableInput
    ) -> UpdateTableOutput:
        table_name = update_table_input["TableName"]
        global_table_region = self.get_global_table_region(context, table_name)

        try:
            self._forward_request(context=context, region=global_table_region)
        except CommonServiceException as exc:
            # DynamoDBLocal refuses to update certain table params and raises.
            # But we still need to update this info in LocalStack stores
            if not (exc.code == "ValidationException" and exc.message == "Nothing to update"):
                raise

            if table_class := update_table_input.get("TableClass"):
                table_definitions = get_store(
                    context.account_id, context.region
                ).table_definitions.setdefault(table_name, {})
                table_definitions["TableClass"] = table_class

            if replica_updates := update_table_input.get("ReplicaUpdates"):
                store = get_store(context.account_id, global_table_region)

                # Dict with source region to set of replicated regions
                replicas: dict[RegionName, ReplicaDescription] = store.REPLICAS.get(table_name, {})

                for replica_update in replica_updates:
                    for key, details in replica_update.items():
                        # Replicated region
                        target_region = details.get("RegionName")

                        # Check if replicated region is valid
                        if target_region not in get_valid_regions_for_service("dynamodb"):
                            raise ValidationException(f"Region {target_region} is not supported")

                        match key:
                            case "Create":
                                if target_region in replicas.keys():
                                    raise ValidationException(
                                        f"Failed to create a the new replica of table with name: '{table_name}' because one or more replicas already existed as tables."
                                    )
                                replicas[target_region] = ReplicaDescription(
                                    RegionName=target_region,
                                    KMSMasterKeyId=details.get("KMSMasterKeyId"),
                                    ProvisionedThroughputOverride=details.get(
                                        "ProvisionedThroughputOverride"
                                    ),
                                    GlobalSecondaryIndexes=details.get("GlobalSecondaryIndexes"),
                                    ReplicaStatus=ReplicaStatus.ACTIVE,
                                )
                            case "Delete":
                                try:
                                    replicas.pop(target_region)
                                except KeyError:
                                    raise ValidationException(
                                        "Update global table operation failed because one or more replicas were not part of the global table."
                                    )

                store.REPLICAS[table_name] = replicas

            # update response content
            SchemaExtractor.invalidate_table_schema(
                table_name, context.account_id, global_table_region
            )

            schema = SchemaExtractor.get_table_schema(
                table_name, context.account_id, global_table_region
            )

            if sse_specification_input := update_table_input.get("SSESpecification"):
                # If SSESpecification is changed, update store and return the 'UPDATING' status in the response
                table_definition = get_store(
                    context.account_id, context.region
                ).table_definitions.setdefault(table_name, {})
                if not sse_specification_input["Enabled"]:
                    table_definition.pop("SSEDescription", None)
                    schema["Table"]["SSEDescription"]["Status"] = "UPDATING"

            return UpdateTableOutput(TableDescription=schema["Table"])

        SchemaExtractor.invalidate_table_schema(table_name, context.account_id, global_table_region)

        schema = SchemaExtractor.get_table_schema(
            table_name, context.account_id, global_table_region
        )

        return UpdateTableOutput(TableDescription=schema["Table"])