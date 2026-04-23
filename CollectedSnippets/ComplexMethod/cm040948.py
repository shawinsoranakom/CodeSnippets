def prepare_transact_write_item_records(
        self,
        account_id: str,
        region_name: str,
        transact_items: TransactWriteItemList,
        existing_items: BatchGetResponseMap,
        updated_items: BatchGetResponseMap,
        tables_stream_type: dict[TableName, TableStreamType],
    ) -> RecordsMap:
        records_only_map: dict[TableName, StreamRecords] = defaultdict(list)

        for request in transact_items:
            record = self.get_record_template(region_name)
            match request:
                case {"Put": {"TableName": table_name, "Item": new_item}}:
                    if not (stream_type := tables_stream_type.get(table_name)):
                        continue
                    keys = SchemaExtractor.extract_keys(
                        item=new_item,
                        table_name=table_name,
                        account_id=account_id,
                        region_name=region_name,
                    )
                    existing_item = find_item_for_keys_values_in_batch(
                        table_name, keys, existing_items
                    )
                    if existing_item == new_item:
                        continue

                    if stream_type.stream_view_type:
                        record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type

                    record["eventID"] = short_uid()
                    record["eventName"] = "INSERT" if not existing_item else "MODIFY"
                    record["dynamodb"]["Keys"] = keys
                    if stream_type.needs_new_image:
                        record["dynamodb"]["NewImage"] = new_item
                    if existing_item and stream_type.needs_old_image:
                        record["dynamodb"]["OldImage"] = existing_item

                    record_item = de_dynamize_record(new_item)
                    record["dynamodb"]["SizeBytes"] = _get_size_bytes(record_item)
                    records_only_map[table_name].append(record)
                    continue

                case {"Update": {"TableName": table_name, "Key": keys}}:
                    if not (stream_type := tables_stream_type.get(table_name)):
                        continue
                    updated_item = find_item_for_keys_values_in_batch(
                        table_name, keys, updated_items
                    )
                    if not updated_item:
                        continue

                    existing_item = find_item_for_keys_values_in_batch(
                        table_name, keys, existing_items
                    )
                    if existing_item == updated_item:
                        # if the item is the same as the previous version, AWS does not send an event
                        continue

                    if stream_type.stream_view_type:
                        record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type

                    record["eventID"] = short_uid()
                    record["eventName"] = "MODIFY" if existing_item else "INSERT"
                    record["dynamodb"]["Keys"] = keys

                    if existing_item and stream_type.needs_old_image:
                        record["dynamodb"]["OldImage"] = existing_item
                    if stream_type.needs_new_image:
                        record["dynamodb"]["NewImage"] = updated_item

                    record["dynamodb"]["SizeBytes"] = _get_size_bytes(updated_item)
                    records_only_map[table_name].append(record)
                    continue

                case {"Delete": {"TableName": table_name, "Key": keys}}:
                    if not (stream_type := tables_stream_type.get(table_name)):
                        continue

                    existing_item = find_item_for_keys_values_in_batch(
                        table_name, keys, existing_items
                    )
                    if not existing_item:
                        continue

                    if stream_type.stream_view_type:
                        record["dynamodb"]["StreamViewType"] = stream_type.stream_view_type

                    record["eventID"] = short_uid()
                    record["eventName"] = "REMOVE"
                    record["dynamodb"]["Keys"] = keys
                    if stream_type.needs_old_image:
                        record["dynamodb"]["OldImage"] = existing_item
                    record_item = de_dynamize_record(existing_item)
                    record["dynamodb"]["SizeBytes"] = _get_size_bytes(record_item)

                    records_only_map[table_name].append(record)
                    continue

        records_map = {
            table_name: TableRecords(
                records=records, table_stream_type=tables_stream_type[table_name]
            )
            for table_name, records in records_only_map.items()
        }

        return records_map