def update_item(
        self,
        context: RequestContext,
        update_item_input: UpdateItemInput,
    ) -> UpdateItemOutput:
        # TODO: UpdateItem is harder to use ReturnValues for Streams, because it needs the Before and After images.
        table_name = update_item_input["TableName"]
        global_table_region = self.get_global_table_region(context, table_name)

        existing_item = None
        stream_type = get_table_stream_type(context.account_id, context.region, table_name)

        # even if we don't need the OldImage, we still need to fetch the existing item to know if the event is INSERT
        # or MODIFY (UpdateItem will create the object if it doesn't exist, and you don't use a ConditionExpression)
        if stream_type:
            existing_item = ItemFinder.find_existing_item(
                put_item=update_item_input,
                table_name=table_name,
                account_id=context.account_id,
                region_name=context.region,
                endpoint_url=self.server.url,
            )

        result = self._forward_request(context=context, region=global_table_region)

        # construct and forward stream record
        if stream_type:
            updated_item = ItemFinder.find_existing_item(
                put_item=update_item_input,
                table_name=table_name,
                account_id=context.account_id,
                region_name=context.region,
                endpoint_url=self.server.url,
            )
            if not updated_item or updated_item == existing_item:
                return result

            record = self.get_record_template(context.region)
            record["eventName"] = "INSERT" if not existing_item else "MODIFY"
            record["dynamodb"]["Keys"] = update_item_input["Key"]
            record["dynamodb"]["SizeBytes"] = _get_size_bytes(updated_item)

            if stream_type.stream_view_type:
                record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type
            if existing_item and stream_type.needs_old_image:
                record["dynamodb"]["OldImage"] = existing_item
            if stream_type.needs_new_image:
                record["dynamodb"]["NewImage"] = updated_item

            records_map = {
                table_name: TableRecords(records=[record], table_stream_type=stream_type)
            }
            self.forward_stream_records(context.account_id, context.region, records_map)

        return result