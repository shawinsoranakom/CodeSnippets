def transact_write_items(
        self,
        context: RequestContext,
        transact_write_items_input: TransactWriteItemsInput,
    ) -> TransactWriteItemsOutput:
        # TODO: add global table support
        existing_items = {}
        existing_items_to_fetch: dict[str, list[Put | Update | Delete]] = {}
        updated_items_to_fetch: dict[str, list[Update]] = {}
        transact_items = transact_write_items_input["TransactItems"]
        tables_stream_type: dict[TableName, TableStreamType] = {}
        no_stream_tables = set()

        for item in transact_items:
            item: TransactWriteItem
            for key in ["Put", "Update", "Delete", "ConditionCheck"]:
                inner_item: Put | Delete | Update = item.get(key)
                if inner_item:
                    # Extract the table name from the ARN; DynamoDB Local does not currently support
                    # full ARNs in this operation: https://github.com/awslabs/amazon-dynamodb-local-samples/issues/34
                    inner_item["TableName"] = table_name = inner_item["TableName"].split(":table/")[
                        -1
                    ]
                    # if we've seen the table already exists and it does not have streams, skip
                    if table_name in no_stream_tables:
                        continue

                    # if we have not seen the table, fetch its streaming status
                    if table_name not in tables_stream_type:
                        if stream_type := get_table_stream_type(
                            context.account_id, context.region, table_name
                        ):
                            tables_stream_type[table_name] = stream_type
                        else:
                            # no stream,
                            no_stream_tables.add(table_name)
                            continue

                    existing_items_to_fetch_for_table = existing_items_to_fetch.setdefault(
                        table_name, []
                    )
                    existing_items_to_fetch_for_table.append(inner_item)
                    if key == "Update":
                        updated_items_to_fetch_for_table = updated_items_to_fetch.setdefault(
                            table_name, []
                        )
                        updated_items_to_fetch_for_table.append(inner_item)

                    continue
        # Normalize the request structure to ensure it matches the expected format for DynamoDB Local.
        data = json.loads(context.request.data)
        data["TransactItems"] = transact_items
        context.request.data = to_bytes(json.dumps(data, cls=BytesEncoder))

        if existing_items_to_fetch:
            existing_items = ItemFinder.find_existing_items(
                put_items_per_table=existing_items_to_fetch,
                account_id=context.account_id,
                region_name=context.region,
                endpoint_url=self.server.url,
            )

        client_token: str | None = transact_write_items_input.get("ClientRequestToken")

        if client_token:
            # we sort the payload since identical payload but with different order could cause
            # IdempotentParameterMismatchException error if a client token is provided
            context.request.data = to_bytes(canonical_json(json.loads(context.request.data)))

        result = self.forward_request(context)

        # determine and forward stream records
        if tables_stream_type:
            updated_items = (
                ItemFinder.find_existing_items(
                    put_items_per_table=existing_items_to_fetch,
                    account_id=context.account_id,
                    region_name=context.region,
                    endpoint_url=self.server.url,
                )
                if updated_items_to_fetch
                else {}
            )

            records_map = self.prepare_transact_write_item_records(
                account_id=context.account_id,
                region_name=context.region,
                transact_items=transact_items,
                existing_items=existing_items,
                updated_items=updated_items,
                tables_stream_type=tables_stream_type,
            )
            self.forward_stream_records(context.account_id, context.region, records_map)

        return result