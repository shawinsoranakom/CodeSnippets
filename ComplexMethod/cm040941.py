def delete_item(
        self,
        context: RequestContext,
        delete_item_input: DeleteItemInput,
    ) -> DeleteItemOutput:
        table_name = delete_item_input["TableName"]
        global_table_region = self.get_global_table_region(context, table_name)

        has_return_values = delete_item_input.get("ReturnValues") == "ALL_OLD"
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

        # determine and forward stream record
        if stream_type:
            # because we modified the request, we will always have the ReturnValues if we have streams enabled
            if has_return_values:
                existing_item = result.get("Attributes")
            else:
                # remove the ReturnValues if the client didn't ask for it
                existing_item = result.pop("Attributes", None)

            if not existing_item:
                return result

            # create record
            record = self.get_record_template(context.region)
            record["eventName"] = "REMOVE"
            record["dynamodb"]["Keys"] = delete_item_input["Key"]
            record["dynamodb"]["SizeBytes"] = _get_size_bytes(existing_item)

            if stream_type.stream_view_type:
                record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type
            if stream_type.needs_old_image:
                record["dynamodb"]["OldImage"] = existing_item

            records_map = {
                table_name: TableRecords(records=[record], table_stream_type=stream_type)
            }
            self.forward_stream_records(context.account_id, context.region, records_map)

        return result