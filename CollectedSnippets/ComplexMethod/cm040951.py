def _add_record(item, comparison_set: ItemSet):
        matching_item = comparison_set.find_item(item)
        if matching_item == item:
            return

        # determine event type
        if comparison_set == after:
            if matching_item:
                return
            event_name = "REMOVE"
        else:
            event_name = "INSERT" if not matching_item else "MODIFY"

        old_image = item if event_name == "REMOVE" else matching_item
        new_image = matching_item if event_name == "REMOVE" else item

        # prepare record
        keys = SchemaExtractor.extract_keys_for_schema(item=item, key_schema=key_schema)

        record = DynamoDBProvider.get_record_template(region_name)
        record["eventName"] = event_name
        record["dynamodb"]["Keys"] = keys
        record["dynamodb"]["SizeBytes"] = _get_size_bytes(item)

        if table_stream_type.stream_view_type:
            record["dynamodb"]["StreamViewType"] = table_stream_type.stream_view_type
        if table_stream_type.needs_new_image:
            record["dynamodb"]["NewImage"] = new_image
        if old_image and table_stream_type.needs_old_image:
            record["dynamodb"]["OldImage"] = old_image

        result.append(record)