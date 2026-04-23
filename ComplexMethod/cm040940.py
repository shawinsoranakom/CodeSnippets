def put_item(self, context: RequestContext, put_item_input: PutItemInput) -> PutItemOutput:
        table_name = put_item_input["TableName"]
        global_table_region = self.get_global_table_region(context, table_name)

        has_return_values = put_item_input.get("ReturnValues") == "ALL_OLD"
        stream_type = get_table_stream_type(context.account_id, context.region, table_name)

        # if the request doesn't ask for ReturnValues and we have stream enabled, we need to modify the request to
        # force DDBLocal to return those values
        if stream_type and not has_return_values:
            service_req = copy.copy(context.service_request)
            service_req["ReturnValues"] = "ALL_OLD"
            result = self._forward_request(
                context=context, region=global_table_region, service_request=service_req
            )
        else:
            result = self._forward_request(context=context, region=global_table_region)

        # Since this operation makes use of global table region, we need to use the same region for all
        # calls made via the inter-service client. This is taken care of by passing the account ID and
        # region, e.g. when getting the stream spec

        # Get stream specifications details for the table
        if stream_type:
            item = put_item_input["Item"]
            # prepare record keys
            keys = SchemaExtractor.extract_keys(
                item=item,
                table_name=table_name,
                account_id=context.account_id,
                region_name=global_table_region,
            )
            # because we modified the request, we will always have the ReturnValues if we have streams enabled
            if has_return_values:
                existing_item = result.get("Attributes")
            else:
                # remove the ReturnValues if the client didn't ask for it
                existing_item = result.pop("Attributes", None)

            if existing_item == item:
                return result

            # create record
            record = self.get_record_template(
                context.region,
            )
            record["eventName"] = "INSERT" if not existing_item else "MODIFY"
            record["dynamodb"]["Keys"] = keys
            record["dynamodb"]["SizeBytes"] = _get_size_bytes(item)

            if stream_type.needs_new_image:
                record["dynamodb"]["NewImage"] = item
            if stream_type.stream_view_type:
                record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type
            if existing_item and stream_type.needs_old_image:
                record["dynamodb"]["OldImage"] = existing_item

            records_map = {
                table_name: TableRecords(records=[record], table_stream_type=stream_type)
            }
            self.forward_stream_records(context.account_id, context.region, records_map)
        return result