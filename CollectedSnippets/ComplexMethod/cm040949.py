def prepare_batch_write_item_records(
        self,
        account_id: str,
        region_name: str,
        tables_stream_type: dict[TableName, TableStreamType],
        request_items: BatchWriteItemRequestMap,
        existing_items: BatchGetResponseMap,
    ) -> RecordsMap:
        records_map: RecordsMap = {}

        # only iterate over tables with streams
        for table_name, stream_type in tables_stream_type.items():
            existing_items_for_table_unordered = existing_items.get(table_name, [])
            table_records: StreamRecords = []

            def find_existing_item_for_keys_values(item_keys: dict) -> AttributeMap | None:
                """
                This function looks up in the existing items for the provided item keys subset. If present, returns the
                full item.
                :param item_keys: the request item keys
                :return:
                """
                keys_items = item_keys.items()
                for item in existing_items_for_table_unordered:
                    if keys_items <= item.items():
                        return item

            for write_request in request_items[table_name]:
                record = self.get_record_template(
                    region_name,
                    stream_view_type=stream_type.stream_view_type,
                )
                match write_request:
                    case {"PutRequest": request}:
                        keys = SchemaExtractor.extract_keys(
                            item=request["Item"],
                            table_name=table_name,
                            account_id=account_id,
                            region_name=region_name,
                        )
                        # we need to find if there was an existing item even if we don't need it for `OldImage`, because
                        # of the `eventName`
                        existing_item = find_existing_item_for_keys_values(keys)
                        if existing_item == request["Item"]:
                            # if the item is the same as the previous version, AWS does not send an event
                            continue
                        record["eventID"] = short_uid()
                        record["dynamodb"]["SizeBytes"] = _get_size_bytes(request["Item"])
                        record["eventName"] = "INSERT" if not existing_item else "MODIFY"
                        record["dynamodb"]["Keys"] = keys

                        if stream_type.needs_new_image:
                            record["dynamodb"]["NewImage"] = request["Item"]
                        if existing_item and stream_type.needs_old_image:
                            record["dynamodb"]["OldImage"] = existing_item

                        table_records.append(record)
                        continue

                    case {"DeleteRequest": request}:
                        keys = request["Key"]
                        if not (existing_item := find_existing_item_for_keys_values(keys)):
                            continue

                        record["eventID"] = short_uid()
                        record["eventName"] = "REMOVE"
                        record["dynamodb"]["Keys"] = keys
                        if stream_type.needs_old_image:
                            record["dynamodb"]["OldImage"] = existing_item
                        record["dynamodb"]["SizeBytes"] = _get_size_bytes(existing_item)
                        table_records.append(record)
                        continue

            records_map[table_name] = TableRecords(
                records=table_records, table_stream_type=stream_type
            )

        return records_map