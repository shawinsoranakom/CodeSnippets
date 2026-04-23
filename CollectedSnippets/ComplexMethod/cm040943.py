def batch_write_item(
        self,
        context: RequestContext,
        batch_write_item_input: BatchWriteItemInput,
    ) -> BatchWriteItemOutput:
        # TODO: add global table support
        existing_items = {}
        existing_items_to_fetch: BatchWriteItemRequestMap = {}
        # UnprocessedItems should have the same format as RequestItems
        unprocessed_items = {}
        request_items = batch_write_item_input["RequestItems"]

        tables_stream_type: dict[TableName, TableStreamType] = {}

        for table_name, items in sorted(request_items.items(), key=itemgetter(0)):
            if stream_type := get_table_stream_type(context.account_id, context.region, table_name):
                tables_stream_type[table_name] = stream_type

            for request in items:
                request: WriteRequest
                for key, inner_request in request.items():
                    inner_request: PutRequest | DeleteRequest
                    if self.should_throttle("BatchWriteItem"):
                        unprocessed_items_for_table = unprocessed_items.setdefault(table_name, [])
                        unprocessed_items_for_table.append(request)

                    elif stream_type:
                        existing_items_to_fetch_for_table = existing_items_to_fetch.setdefault(
                            table_name, []
                        )
                        existing_items_to_fetch_for_table.append(inner_request)

        if existing_items_to_fetch:
            existing_items = ItemFinder.find_existing_items(
                put_items_per_table=existing_items_to_fetch,
                account_id=context.account_id,
                region_name=context.region,
                endpoint_url=self.server.url,
            )

        try:
            result = self.forward_request(context)
        except CommonServiceException as e:
            # TODO: validate if DynamoDB still raises `One of the required keys was not given a value`
            # for now, replace with the schema error validation
            if e.message == "One of the required keys was not given a value":
                raise ValidationException("The provided key element does not match the schema")
            raise e

        # determine and forward stream records
        if tables_stream_type:
            records_map = self.prepare_batch_write_item_records(
                account_id=context.account_id,
                region_name=context.region,
                tables_stream_type=tables_stream_type,
                request_items=request_items,
                existing_items=existing_items,
            )
            self.forward_stream_records(context.account_id, context.region, records_map)

        # TODO: should unprocessed item which have mutated by `prepare_batch_write_item_records` be returned
        for table_name, unprocessed_items_in_table in unprocessed_items.items():
            unprocessed: dict = result["UnprocessedItems"]
            result_unprocessed_table = unprocessed.setdefault(table_name, [])

            # add the Unprocessed items to the response
            # TODO: check before if the same request has not been Unprocessed by DDB local already?
            # those might actually have been processed? shouldn't we remove them from the proxied request?
            for request in unprocessed_items_in_table:
                result_unprocessed_table.append(request)

            # remove any table entry if it's empty
            result["UnprocessedItems"] = {k: v for k, v in unprocessed.items() if v}

        return result